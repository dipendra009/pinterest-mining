--
--  Copyright (c) 2014, Facebook, Inc.
--  All rights reserved.
--
--  This source code is licensed under the BSD-style license found in the
--  LICENSE file in the root directory of this source tree. An additional grant
--  of patent rights can be found in the PATENTS file in the same directory.
--
--  VERSION mytest2
--    calculate top 1~10

testLogger = optim.Logger(paths.concat(opt.save, 'test.log'))

local testDataIterator = function()
   testLoader:reset()
   return function() return testLoader:get_batch(false) end
end

local batchNumber
local topN_center, topX_center, loss
local test_counts
local topN_counts, topX_counts


function test()
   print('==> doing epoch on validation data:')
   print("==> testing epoch # " .. epoch) -- #RL: epoch is global var set in main.lua

   batchNumber = 0
   cutorch.synchronize()
   local timer = torch.Timer()
   timer:reset()
   -- set the dropouts to evaluate mode
   model:evaluate()

   topN_center = {}
   for i=1,10 do
       topN_center[i] = 0
   end
   
   topX_center = 0
   test_counts = {}
   topN_counts = {}
   for i=1,10 do
       topN_counts[i] = {}
   end

   topX_counts = {}
   loss = 0

   X_bar = opt.topXbar -- a threshold set so that x is determined by the sum of top x probability predictions exceeds it
   X_mean = 0.0
   X_min = nClasses
   X_max = 1

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

   for i=1,10 do
       topN_center[i] = topN_center[i] * 100 / nTest
   end
   topX_center = topX_center * 100 / nTest

   loss = loss / (nTest/opt.testBatchSize) -- because loss is calculated per batch
   testLogger:add{
      ['% top1 accuracy'] = topN_center[1],
      ['% top2 accuracy'] = topN_center[2],
      ['% top3 accuracy'] = topN_center[3],
      ['% top4 accuracy'] = topN_center[4],
      ['% top5 accuracy'] = topN_center[5],
      ['% top6 accuracy'] = topN_center[6],
      ['% top7 accuracy'] = topN_center[7],
      ['% top8 accuracy'] = topN_center[8],
      ['% top9 accuracy'] = topN_center[9],
      ['% top10 accuracy'] = topN_center[10],
      ['% topX accuracy'] = topX_center,
      ['avg loss'] = loss
   }
   print(string.format('Epoch: [%d][TESTING SUMMARY] Total Time(s): %.2f\t'
                          .. 'average loss (per batch): %.2f\t'
                          .. 'accuracy [Center](%%):\t top1 %.2f\t top5 %.2f\t top10 %.2f\t topX %.2f\t',
                      --    .. 'X statistics (bar=%f):\t X mean %.2f\t X min %d\t X max %d',
                       epoch, timer:time().real, loss, topN_center[1], topN_center[5], topN_center[10], topX_center)) --, X_bar, X_mean, X_min, X_max))

   print(string.format('Epoch: [%d][TOPX SUMMARY]\t'
                          .. 'X statistics (bar=%f):\t X mean %.2f\t X min %d\t X max %d',
                       epoch, X_bar, X_mean, X_min, X_max))

   print('\n')
   assert(#test_counts == #topN_counts[1] and #test_counts == #topN_counts[5] and #test_counts == #topN_counts[10], "counts variable mismatch!")
   print(string.format('Epoch: [%d][CLASSBREAKDOWN]\tlabel\t\t\ttotalCases\ttop1\ttop2\ttop3\ttop4\ttop5\ttop6\ttop7\ttop8\ttop9\ttop10',epoch))
   --for i=1,#test_counts do
   --  print(string.format('Epoch: [%d][CLASSBREAKDOWN]\t%s\t\t\t%d\t%d\t%d\t%d\%d\t%d\t%d\t%d\t%d\t%d\t%d\t',
   --   epoch,classes[i],test_counts[i],topN_counts[1][i],topN_counts[2][i],topN_counts[3][i],topN_counts[4][i],topN_counts[5][i],topN_counts[6][i],topN_counts[7][i],topN_counts[8][i],topN_counts[9][i],topN_counts[10][i]))
   --end
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

    local pp, pred_sorted = pred:sort(2, true) -- pred_sorted is a list of sorted labels, pp is sorted log probs
    for i=1,pred:size(1) do
       local g = labelsCPU[i] -- true label of the test image
       if test_counts[g] then
         test_counts[g] = test_counts[g]+1
       else
         test_counts[g] = 1
         topX_counts[g] = 0
         for k=1,10 do
             topN_counts[k][g] = 0
         end
       end
       -- determine x
       local x = 1
       local current_bar = torch.exp(pp[i][1])
       while current_bar < X_bar do
           x = x+1
           current_bar = current_bar + torch.exp(pp[i][x])
       end
       -- x is determined for each test case
       X_mean = X_mean*(nTest-1)/nTest + x/nTest -- running average
       if x < X_min then X_min = x end
       if x > X_max then X_max = x end
       -- stats of x updated

       if pred_sorted[i][1] == g then
         topN_center[1] = topN_center[1] + 1
         topN_counts[1][g] = topN_counts[1][g]+1
       end
       for k=2,10 do
           for j = 1,k do -- top k
            if pred_sorted[i][j] == g then
              topN_center[k] = topN_center[k] + 1
              topN_counts[k][g] = topN_counts[k][g]+1
            end
           end
       end
       for j = 1,x do -- top x
        if pred_sorted[i][j] == g then
          topX_center = topX_center + 1
          topX_counts[g] = topX_counts[g]+1
        end
       end
    end
   if batchNumber % 1024 == 0 then
      print(('Epoch: Testing [%d][%d/%d]'):format(epoch, batchNumber, nTest))
   end
end
