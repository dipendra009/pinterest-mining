require 'fbcunn'
require 'cudnn'

function createModel(nGPU)
   assert(nGPU == 1 or nGPU == 2, '1-GPU or 2-GPU supported for AlexNet')
   local features
   if nGPU == 1 then
      features = nn.Concat(2)
   else
      require 'fbnn'
      features = nn.ModelParallel(2)
   end

   local fb1 = nn.Sequential() -- branch 1
   -- 16,2016,7: batch of 16. 84days*24hr/d=2016 frames. 7 dimsions.
   fb1:add(nn.TemporalConvolutionFB(7,48,11,4))       -- 16,2016,7 -> 16,502,48
   fb1:add(cudnn.ReLU(true))
   fb1:add(nn.TemporalMaxPooling(3,2))                -- 16,502,48 -> 16,250,48
   fb1:add(nn.TemporalConvolutionFB(48,128,5,1))      -- 16,250,48 -> 16,246,128
   fb1:add(cudnn.ReLU(true))
   fb1:add(nn.TemporalMaxPooling(3,2))                -- 16,246,128 -> 16,122,128
   fb1:add(nn.TemporalConvolutionFB(128,192,3,1))     -- 16,122,128 -> 16,120,192
   fb1:add(cudnn.ReLU(true))
   fb1:add(nn.TemporalConvolutionFB(192,192,3,1))     -- 16,120,192 -> 16,118,192
   fb1:add(cudnn.ReLU(true))
   fb1:add(nn.TemporalConvolutionFB(192,128,3,1))     -- 16,118,192 -> 16 116,128
   fb1:add(cudnn.ReLU(true))
   fb1:add(nn.TemporalMaxPooling(3,2))                -- 16 116,128 -> 16,57,128

   local fb2 = fb1:clone() -- branch 2
   for k,v in ipairs(fb2:findModules('nn.TemporalConvolutionFB')) do
      v:reset() -- reset branch 2's weights
   end

   features:add(fb1)
   features:add(fb2)

   -- 1.3. Create Classifier (fully connected layers)
   local classifier = nn.Sequential()
   classifier:add(nn.View(57*128*2))
   classifier:add(nn.Dropout(0.5))
   classifier:add(nn.Linear(57*128*2, 4096))
   classifier:add(nn.Threshold(0, 1e-6))
   classifier:add(nn.Dropout(0.5))
   classifier:add(nn.Linear(4096, 4096))
   classifier:add(nn.Threshold(0, 1e-6))
   classifier:add(nn.Linear(4096, nClasses))
   classifier:add(nn.LogSoftMax())

   -- 1.4. Combine 1.1 and 1.3 to produce final model
   local model = nn.Sequential():add(features):add(classifier)

   return model
end
