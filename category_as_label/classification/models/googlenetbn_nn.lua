
local function inception(input_size, config)
   local concat = nn.Concat(2)
   if config[1][1] ~= 0 then
      local conv1 = nn.Sequential()
      conv1:add(nn.SpatialConvolution(input_size, config[1][1],1,1,1,1)):add(nn.SpatialBatchNormalization(config[1][1],1e-3)):add(nn.ReLU())
      concat:add(conv1)
   end

   local conv3 = nn.Sequential()
   conv3:add(nn.SpatialConvolution(  input_size, config[2][1],1,1,1,1)):add(nn.SpatialBatchNormalization(    config[2][1],1e-3)):add(nn.ReLU())
   conv3:add(nn.SpatialConvolution(config[2][1], config[2][2],3,3,1,1,1,1)):add(nn.SpatialBatchNormalization(config[2][2],1e-3)):add(nn.ReLU())
   concat:add(conv3)

   local conv3xx = nn.Sequential()
   conv3xx:add(nn.SpatialConvolution(  input_size, config[3][1],1,1,1,1)):add(nn.SpatialBatchNormalization(    config[3][1],1e-3)):add(nn.ReLU())
   conv3xx:add(nn.SpatialConvolution(config[3][1], config[3][2],3,3,1,1,1,1)):add(nn.SpatialBatchNormalization(config[3][2],1e-3)):add(nn.ReLU())
   conv3xx:add(nn.SpatialConvolution(config[3][2], config[3][2],3,3,1,1,1,1)):add(nn.SpatialBatchNormalization(config[3][2],1e-3)):add(nn.ReLU())
   concat:add(conv3xx)

   local pool = nn.Sequential()
   pool:add(nn.SpatialZeroPadding(1,1,1,1)) -- remove after getting nn R2 into fbcode
   if config[4][1] == 'max' then
      pool:add(nn.SpatialMaxPooling(3,3,1,1):ceil())
   elseif config[4][1] == 'avg' then
      pool:add(nn.SpatialAveragePooling(3,3,1,1)) -- use floor mode here.
   else
      error('Unknown pooling')
   end
   if config[4][2] ~= 0 then
      pool:add(nn.SpatialConvolution(input_size, config[4][2],1,1,1,1)):add(nn.SpatialBatchNormalization(config[4][2],1e-3)):add(nn.ReLU())
   end
   concat:add(pool)

   return concat
end

function createModel()
   local features = nn.Sequential()
   features:add(nn.SpatialConvolution(3,64,7,7,2,2,3,3)):add(nn.SpatialBatchNormalization(64,1e-3)):add(nn.ReLU())
   features:add(nn.SpatialMaxPooling(3,3,2,2):ceil())
   features:add(nn.SpatialConvolution(64,64,1,1)):add(nn.SpatialBatchNormalization(64,1e-3)):add(nn.ReLU())
   features:add(nn.SpatialConvolution(64,192,3,3,1,1,1,1)):add(nn.SpatialBatchNormalization(192,1e-3)):add(nn.ReLU())
   features:add(nn.SpatialMaxPooling(3,3,2,2):ceil())
   features:add(inception( 192, {{ 64},{ 64, 64},{ 64, 96},{'avg', 32}})) -- 3(a)
   features:add(inception( 256, {{ 64},{ 64, 96},{ 64, 96},{'avg', 64}})) -- 3(b)
   features:add(inception( 320, {{  0},{128,160},{ 64, 96},{'max',  0}})) -- 3(c)
   features:add(nn.SpatialConvolution(576,576,2,2,2,2)):add(nn.SpatialBatchNormalization(576,1e-3))
   features:add(inception( 576, {{224},{ 64, 96},{ 96,128},{'avg',128}})) -- 4(a)
   features:add(inception( 576, {{192},{ 96,128},{ 96,128},{'avg',128}})) -- 4(b)
   features:add(inception( 576, {{160},{128,160},{128,160},{'avg', 96}})) -- 4(c)
   features:add(inception( 576, {{ 96},{128,192},{160,192},{'avg', 96}})) -- 4(d)

   local main_branch = nn.Sequential()
   main_branch:add(inception( 576, {{  0},{128,192},{192,256},{'max',  0}})) -- 4(e)
   main_branch:add(nn.SpatialConvolution(1024,1024,2,2,2,2)):add(nn.SpatialBatchNormalization(1024,1e-3))
   main_branch:add(inception(1024, {{352},{192,320},{160,224},{'avg',128}})) -- 5(a)
   main_branch:add(inception(1024, {{352},{192,320},{192,224},{'max',128}})) -- 5(b)
   main_branch:add(nn.SpatialAveragePooling(7,7,1,1))
   main_branch:add(nn.View(1024):setNumInputDims(3))
   main_branch:add(nn.Linear(1024,nClasses))
   main_branch:add(nn.LogSoftMax())


   local model = nn.Sequential():add(features):add(main_branch)

   return model
end
