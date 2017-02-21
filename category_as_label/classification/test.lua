--
--  Copyright (c) 2014, Facebook, Inc.
--  All rights reserved.
--
--  This source code is licensed under the BSD-style license found in the
--  LICENSE file in the root directory of this source tree. An additional grant
--  of patent rights can be found in the PATENTS file in the same directory.
--
testLogger = optim.Logger(paths.concat(opt.save, 'test.log'))

local testDataIterator = function()
   testLoader:reset()
   return function() return testLoader:get_batch(false) end
end

local batchNumber
local top1_center, top5_center, loss
local test_counts
local top1_counts
local top5_counts

function test()
   print('==> doing epoch on validation data:')
   print("==> testing epoch # " .. epoch) -- #RL: epoch is global var set in main.lua

   batchNumber = 0
   cutorch.synchronize()
   local timer = torch.Timer()
   timer:reset()
   -- set the dropouts to evaluate mode
   model:evaluate()

   top1_center = 0
   top5_center = 0
   top10_center = 0
   test_counts = {}
   top1_counts = {}
   top5_counts = {}
   top10_counts = {}
   loss = 0
   for i=1,nTest/opt.testBatchSize do -- nTest is set in 1_data.lua
      local indexStart = (i-1) * opt.testBatchSize + 1
      local indexEnd = (indexStart + opt.testBatchSize - 1)
      donkeys:addjob(
         -- work to be done by donkey thread
         function()
            local inputs, labels = testLoader:get(indexStart, indexEnd)
            return sendTensor(inputs), sendTensor(labels)
         end,
         -- callback that is run in the main thread once the work is done
         testBatch
      )
   end

   donkeys:synchronize()
   cutorch.synchronize()

   top1_center = top1_center * 100 / nTest
   top5_center = top5_center * 100 / nTest
   top10_center = top10_center * 100 / nTest

   loss = loss / (nTest/opt.testBatchSize) -- because loss is calculated per batch
   testLogger:add{
      ['% top1 accuracy (test set) (center crop)'] = top1_center,
      ['% top5 accuracy (test set) (center crop)'] = top5_center,
      ['% top10 accuracy (test set) (center crop)'] = top10_center,
      ['avg loss (test set)'] = loss
   }
   print(string.format('Epoch: [%d][TESTING SUMMARY] Total Time(s): %.2f\t'
                          .. 'average loss (per batch): %.2f\t '
                          .. 'accuracy [Center](%%):\t top-1 %.2f\t top-5 %.2f\t top-10 %.2f\t',
                       epoch, timer:time().real, loss, top1_center, top5_center, top10_center))

   print('\n')
   assert(#test_counts == #top1_counts and #test_counts == #top5_counts and #test_counts == #top10_counts, "counts variable mismatch!")
   print(string.format('Epoch: [%d][CLASSBREAKDOWN]\tlabel\ttotalCases\ttop1\ttop5\ttop10',epoch))
   for i=1,#test_counts do
     print(string.format('Epoch: [%d][CLASSBREAKDOWN]\t%s\t%d\t%d\t%d\t%d',
      epoch,classes[i],test_counts[i],top1_counts[i],top5_counts[i],top10_counts[i]))
   end
   collectgarbage()

end -- of test()
-----------------------------------------------------------------------------
local inputsCPU = torch.FloatTensor()
local labelsCPU = torch.LongTensor()
local inputs = torch.CudaTensor()
local labels = torch.CudaTensor()

function testBatch(inputsThread, labelsThread)
   batchNumber = batchNumber + opt.testBatchSize

   receiveTensor(inputsThread, inputsCPU)
   receiveTensor(labelsThread, labelsCPU)
   inputs:resize(inputsCPU:size()):copy(inputsCPU)
   labels:resize(labelsCPU:size()):copy(labelsCPU)

   local outputs = model:forward(inputs)
   local err = criterion:forward(outputs, labels)
   cutorch.synchronize()
   local pred = outputs:float()

   loss = loss + err

    local pp, pred_sorted = pred:sort(2, true)
    for i=1,pred:size(1) do
       local g = labelsCPU[i]
       if test_counts[g] then
         test_counts[g] = test_counts[g]+1
       else
         test_counts[g] = 1
         top1_counts[g] = 0
         top5_counts[g] = 0
         top10_counts[g] = 0
       end
       if pred_sorted[i][1] == g then
         top1_center = top1_center + 1
         top1_counts[g] = top1_counts[g]+1
       end
       for j = 1,5 do
        if pred_sorted[i][j] == g then
          top5_center = top5_center + 1
          top5_counts[g] = top5_counts[g]+1
        end
       end
       for j = 1,10 do
        if pred_sorted[i][j] == g then
          top10_center = top10_center + 1
          top10_counts[g] = top10_counts[g]+1
        end
       end
    end
   if batchNumber % 1024 == 0 then
      print(('Epoch: Testing [%d][%d/%d]'):format(epoch, batchNumber, nTest))
   end
end
