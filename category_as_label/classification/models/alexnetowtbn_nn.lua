function createModel(nGPU)
   -- from https://code.google.com/p/cuda-convnet2/source/browse/layers/layers-imagenet-1gpu.cfg
   -- this is AlexNet that was presented in the One Weird Trick paper. http://arxiv.org/abs/1404.5997
   local features = nn.Sequential()
   features:add(nn.SpatialConvolution(3,64,11,11,4,4,2,2))       -- 224 -> 55
   features:add(nn.SpatialBatchNormalization(64,1e-3))
   features:add(nn.ReLU())
   features:add(nn.SpatialMaxPooling(3,3,2,2))                   -- 55 ->  27
   features:add(nn.SpatialConvolution(64,192,5,5,1,1,2,2))       --  27 -> 27
   features:add(nn.SpatialBatchNormalization(192,1e-3))
   features:add(nn.ReLU())
   features:add(nn.SpatialMaxPooling(3,3,2,2))                   --  27 ->  13
   features:add(nn.SpatialConvolution(192,384,3,3,1,1,1,1))      --  13 ->  13
   features:add(nn.SpatialBatchNormalization(384,1e-3))
   features:add(nn.ReLU())
   features:add(nn.SpatialConvolution(384,256,3,3,1,1,1,1))      --  13 ->  13
   features:add(nn.SpatialBatchNormalization(256,1e-3))
   features:add(nn.ReLU())
   features:add(nn.SpatialConvolution(256,256,3,3,1,1,1,1))      --  13 ->  13
   features:add(nn.SpatialBatchNormalization(256,1e-3))
   features:add(nn.ReLU())
   features:add(nn.SpatialMaxPooling(3,3,2,2))                   -- 13 -> 6

   local classifier = nn.Sequential()
   classifier:add(nn.View(256*6*6))

   local branch1 = nn.Concat(2)

   for i=1,nGPU do
      local s = nn.Sequential()
      s:add(nn.Linear(256*6*6, 4096/nGPU))
      s:add(nn.BatchNormalization(4096/nGPU,1e-3))
      s:add(nn.ReLU())
      branch1:add(s)
   end
   classifier:add(branch1)

   local branch2 = nn.Concat(2)

   for i=1,nGPU do
      local s = nn.Sequential()
      s:add(nn.Linear(4096, 4096/nGPU))
      s:add(nn.BatchNormalization(4096/nGPU,1e-3))
      s:add(nn.ReLU())
      branch2:add(s)
   end
   classifier:add(branch2)
   classifier:add(nn.Linear(4096, nClasses))
   classifier:add(nn.LogSoftMax())

   local model = nn.Sequential():add(features):add(classifier)
   return model
end
