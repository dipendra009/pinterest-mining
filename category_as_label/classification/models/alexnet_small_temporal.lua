require 'cunn'
-- smaller temporal alexnet using just cunn (w/o fbcunn or cudnn)
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
   fb1:add(nn.TemporalConvolution(7,24,11,4))       -- 16,2016,7 -> 16,502,24
   fb1:add(nn.ReLU(true))
   fb1:add(nn.TemporalMaxPooling(3,2))                -- 16,502,24 -> 16,250,24
   fb1:add(nn.TemporalConvolution(24,64,5,1))       -- 16,250,24 -> 16,246,64
   fb1:add(nn.ReLU(true))
   fb1:add(nn.TemporalMaxPooling(3,2))                -- 16,246,64 -> 16,122,64
   fb1:add(nn.TemporalConvolution(64,96,3,1))       -- 16,122,64 -> 16,120,96
   fb1:add(nn.ReLU(true))
   fb1:add(nn.TemporalConvolution(96,96,3,1))       -- 16,120,96 -> 16,118,96
   fb1:add(nn.ReLU(true))
   fb1:add(nn.TemporalConvolution(96,64,3,1))       -- 16,118,96 -> 16 116,64
   fb1:add(nn.ReLU(true))
   fb1:add(nn.TemporalMaxPooling(3,2))                -- 16 116,64 -> 16,57,64

   local fb2 = fb1:clone() -- branch 2
   for k,v in ipairs(fb2:findModules('nn.TemporalConvolution')) do
      v:reset() -- reset branch 2's weights
   end

   features:add(fb1)
   features:add(fb2)

   -- 1.3. Create Classifier (fully connected layers)
   local classifier = nn.Sequential()
   classifier:add(nn.View(57*64*2))
   classifier:add(nn.Dropout(0.5))
   classifier:add(nn.Linear(57*64*2, 1024))
   classifier:add(nn.Threshold(0, 1e-6))
   classifier:add(nn.Dropout(0.5))
   classifier:add(nn.Linear(1024, 1024))
   classifier:add(nn.Threshold(0, 1e-6))
   classifier:add(nn.Linear(1024, nClasses))
   classifier:add(nn.LogSoftMax())

   -- 1.4. Combine 1.1 and 1.3 to produce final model
   local model = nn.Sequential():add(features):add(classifier)

   return model
end
