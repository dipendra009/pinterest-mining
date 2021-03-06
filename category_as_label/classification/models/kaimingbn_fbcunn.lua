function createModel(nGPU)
   require 'cudnn'
   require 'fbcunn'
   -- no dropouts b/c using batch normalization
   -- from https://code.google.com/p/cuda-convnet2/source/browse/layers/layers-imagenet-1gpu.cfg
   -- Yves' net
   local features = nn.Sequential()
   features:add(cudnn.SpatialConvolution(3,64,11,11,4,4,2,2))       -- 224 -> 55 -- fbfft only supports stride of 1
   features:add(nn.SpatialBatchNormalization(64,1e-3))
   features:add(cudnn.ReLU(true))
   features:add(cudnn.SpatialMaxPooling(3,3,2,2))                   -- 55 ->  27
   features:add(nn.SpatialZeroPadding(2,2,2,2))
   features:add(nn.SpatialConvolutionCuFFT(64,128,5,5,1,1))       --  27 -> 27
   features:add(nn.SpatialBatchNormalization(128,1e-3))
   features:add(cudnn.ReLU(true))
   features:add(cudnn.SpatialMaxPooling(3,3,2,2))                   --  27 ->  13
   features:add(nn.SpatialZeroPadding(1,1,1,1))
   features:add(nn.SpatialConvolutionCuFFT(128,192,3,3,1,1))      --  13 ->  13
   features:add(cudnn.ReLU(true))
   features:add(nn.SpatialZeroPadding(1,1,1,1))
   features:add(nn.SpatialConvolutionCuFFT(192,128,3,3,1,1))      --  13 ->  13
   features:add(cudnn.ReLU(true))
   features:add(nn.SpatialZeroPadding(1,1,1,1))
   features:add(nn.SpatialConvolutionCuFFT(128,128,3,3,1,1))      --  13 ->  13
   features:add(nn.SpatialBatchNormalization(128,1e-3))
   features:add(cudnn.ReLU(true))
   features:add(cudnn.SpatialMaxPooling(3,3,2,2))                   -- 13 -> 6
   if nGPU > 1 then
      assert(nGPU <= cutorch.getDeviceCount(), 'number of GPUs less than nGPU specified')
      local features_single = features
      features = nn.DataParallel(1)
      for i=1,nGPU do
         cutorch.withDevice(i, function()
                               features:add(features_single:clone())
         end)
      end
      features.gradInput = nil
   end

   local classifier = nn.Sequential()
   classifier:add(nn.View(128*6*6))

   local branch1
   if nGPU == 1 then
      branch1 = nn.Concat(2)
   else
      branch1 = nn.ModelParallel(2)
   end
   for i=1,nGPU do
      local s = nn.Sequential()
      s:add(nn.Linear(128*6*6, 2048/nGPU))
      s:add(nn.BatchNormalization(2048/nGPU,1e-3))
      s:add(nn.ReLU())
      branch1:add(s)
   end
   classifier:add(branch1)
   local branch2
   if nGPU == 1 then
      branch2 = nn.Concat(2)
   else
      branch2 = nn.ModelParallel(2)
   end
   for i=1,nGPU do
      local s = nn.Sequential()
      s:add(nn.Linear(2048, 2048/nGPU))
      s:add(nn.BatchNormalization(2048/nGPU,1e-3))
      s:add(nn.ReLU())
      branch2:add(s)
   end
   classifier:add(branch2)
   classifier:add(nn.Linear(2048, nClasses))
   classifier:add(nn.LogSoftMax())

   local model = nn.Sequential():add(features):add(classifier)

   return model
end
