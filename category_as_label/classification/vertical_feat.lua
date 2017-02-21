--
--  Copyright (c) 2014, Facebook, Inc.
--  All rights reserved.
--
--  This source code is licensed under the BSD-style license found in the
--  LICENSE file in the root directory of this source tree. An additional grant
--  of patent rights can be found in the PATENTS file in the same directory.
--
-- Like test.lua, only counts the ones in given vertical.
testLogger = optim.Logger(paths.concat(opt.save, 'test.log'))

local testDataIterator = function()
   testLoader:reset()
   return function() return testLoader:get_batch(false) end
end
function table.contains(table, element)
  for _, value in pairs(table) do
    if value == element then
      return true
    end
  end
  return false
end

local batchNumber
local verticalClasses
local batchFeatures
local output_labels,output_features
local outf,outff
function test(verticalFile)
   print('==> doing epoch on validation data:')
   print("==> online epoch # " .. epoch)

   batchNumber = 0
   cutorch.synchronize()
   local timer = torch.Timer()
   timer:reset()
   -- set the dropouts to evaluate mode
   model:evaluate()

   output_labels = {}
   output_features = {}
   verticalClasses = torch.load(verticalFile)
   outf = io.open(verticalFile..'.label_feature.txt', "w")
   outff= io.open(verticalFile..'.accuracy_dump.txt', "w")

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

   outf:close()
   outff:close()
   print('saving output labels...')
   torch.save(verticalFile..'.labels.t7', output_labels)

   print('saving output features...')
   torch.save(verticalFile..'.features.t7', output_features)
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
   cutorch.synchronize()
   local pred = outputs:float()

   -- module indices only works for alexnetowtbn.
   -- use modules[2].modules[3] to access the last feature layer.
   -- use modules[2].modules[4] to access the final nCqlasses layer.
   --batchFeatures = model.modules[2].modules[4].output
   batchFeatures = outputs
   local pp, pred_sorted = pred:sort(2, true)

   for i=1,batchFeatures:size(1) do
      local g = labelsCPU[i]
      local bool_x = 1
      for j = 1,pred_sorted:size(2) do
       if pred_sorted[i][j] == g then
         -- 1st num. is the global predidction. e.g., 1 is top1, 1,2,3,4,5 are counted as top 5
         -- 2nd num. is vertical specific. 1 would be top1 given the prediction is made within vertical.
         outff:write(('%d\t%d\n'):format(j,bool_x))
         break
       elseif table.contains(verticalClasses,classes[pred_sorted[i][j]]) then
         bool_x = bool_x + 1
       end
      end



      table.insert(output_features, batchFeatures[i]:float())
      if table.contains(verticalClasses,classes[g]) then
        table.insert(output_labels, 1)
      else
        table.insert(output_labels, -1)
      end
      outf:write(('%d'):format(output_labels[#output_labels]))
      local v = output_features[#output_features]
      v = torch.exp(v)
      for j=1,v:size(1) do
        if (v[j] > 0.01) then
        --if (v[j] > 0.001) and table.contains(verticalClasses,classes[j]) then
          outf:write((' %d:%.5f'):format(j,v[j]))
        end
      end
      outf:write('\n')
   end
   if batchNumber % 1024 == 0 then
      print(('Epoch: Testing [%d][%d/%d]'):format(epoch, batchNumber, nTest))
   end
end
