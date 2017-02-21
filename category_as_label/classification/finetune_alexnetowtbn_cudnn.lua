--converts alexnet_cudnn to CPU nn. tested w/ 1 GPU
-- for nGPU > 1. on need to copy data parallel. parameter in each data parallel
-- module is identical. change modelParallel to Concat.
-- only works for cudnn model. as the layer numbering in fbcunn is different due to added
--   zeopadding layers.
torch.setdefaulttensortype('torch.FloatTensor')
require 'nn'
require 'torch'
require 'paths'
require 'cudnn'

nClasses=989
paths.dofile('models/alexnetowtbn_cudnn.lua')
gpus = {1} -- the model layout changes as number of GPUs changes.
local cpumodel = createModel(#gpus) -- be consistent with how many gpus we want to use in the subsequent training


local gpumodel_path = '../pretrainer_alexowtbn.t7'
local cpumodel_path = '../pretrainee_alexowtbn.t7'

local gpumodel,criterion
gpumodel = torch.load(gpumodel_path)


-- spatial conv.
for _,i in pairs({1,5,9,12,15}) do -- conv layers in alex owt bn
  local cpu_conv_mod = cpumodel.modules[1].modules[i]
  local gpu_conv_mod
  if #gpus > 1 then
    gpu_conv_mod = gpumodel.modules[1].modules[1].modules[i]
  else
    gpu_conv_mod = gpumodel.modules[1].modules[i]
  end
  local w  = gpu_conv_mod.weight
  local b  = gpu_conv_mod.bias
  local gw = gpu_conv_mod.gradWeight
  local gb = gpu_conv_mod.gradBias
  print('processing conv ..'..tostring(i))
  cpu_conv_mod.weight = torch.CudaTensor(w:size()):copy(w)
  cpu_conv_mod.bias = torch.CudaTensor(b:size()):copy(b)
  cpu_conv_mod.gradWeight = torch.CudaTensor(gw:size()):copy(gw)
  cpu_conv_mod.gradBias = torch.CudaTensor(gb:size()):copy(gb)
end

-- spatial batch norm.
for _,i in pairs({2,6,10,13,16}) do -- spatial batch norm layers in alex owt bn
  local cpu_bn_mod = cpumodel.modules[1].modules[i]
  local gpu_bn_mod
  if #gpus > 1 then
    gpu_bn_mod = gpumodel.modules[1].modules[1].modules[i]
  else
    gpu_bn_mod = gpumodel.modules[1].modules[i]
  end
  local w  = gpu_bn_mod.weight
  local b  = gpu_bn_mod.bias
  local gw = gpu_bn_mod.gradWeight
  local gb = gpu_bn_mod.gradBias
  local rm = gpu_bn_mod.running_mean
  local rs = gpu_bn_mod.running_std
  print('processing bn ..'..tostring(i))
  cpu_bn_mod.weight = torch.CudaTensor(w:size()):copy(w)
  cpu_bn_mod.bias = torch.CudaTensor(b:size()):copy(b)
  cpu_bn_mod.gradWeight = torch.CudaTensor(gw:size()):copy(gw)
  cpu_bn_mod.gradBias = torch.CudaTensor(gb:size()):copy(gb)
  cpu_bn_mod.running_mean = torch.CudaTensor(rm:size()):copy(rm)
  cpu_bn_mod.running_std = torch.CudaTensor(rs:size()):copy(rs)
end


-- linear layers
for _,i in pairs({2,3}) do
  for _,j in pairs(gpus) do
    local cpu_lin_mod = cpumodel.modules[2].modules[i].modules[j].modules[1]
    local gpu_lin_mod = gpumodel.modules[2].modules[i].modules[j].modules[1]
    local w  = gpu_lin_mod.weight
    local b  = gpu_lin_mod.bias
    local gw = gpu_lin_mod.gradWeight
    local gb = gpu_lin_mod.gradBias
    print('processing concat linear ..'..tostring(i))
    cpu_lin_mod.weight = torch.CudaTensor(w:size()):copy(w)
    cpu_lin_mod.bias = torch.CudaTensor(b:size()):copy(b)
    cpu_lin_mod.gradWeight = torch.CudaTensor(gw:size()):copy(gw)
    cpu_lin_mod.gradBias = torch.CudaTensor(gb:size()):copy(gb)
  end
end

-- batch norm.
for _,i in pairs({2,3}) do
  for _,j in pairs(gpus) do
    local cpu_lin_mod = cpumodel.modules[2].modules[i].modules[j].modules[2]
    local gpu_lin_mod = gpumodel.modules[2].modules[i].modules[j].modules[2]
    local w  = gpu_lin_mod.weight
    local b  = gpu_lin_mod.bias
    local gw = gpu_lin_mod.gradWeight
    local gb = gpu_lin_mod.gradBias
    local rm = gpu_lin_mod.running_mean
    local rs = gpu_lin_mod.running_std
    print('processing concat bn ..'..tostring(i))
    cpu_lin_mod.weight = torch.CudaTensor(w:size()):copy(w)
    cpu_lin_mod.bias = torch.CudaTensor(b:size()):copy(b)
    cpu_lin_mod.gradWeight = torch.CudaTensor(gw:size()):copy(gw)
    cpu_lin_mod.gradBias = torch.CudaTensor(gb:size()):copy(gb)
    cpu_lin_mod.running_mean = torch.CudaTensor(rm:size()):copy(rm)
    cpu_lin_mod.running_std = torch.CudaTensor(rs:size()):copy(rs)
  end
end

-- Omit the last linear layer since the nClasses are different

--for _,i in pairs({4}) do
--  local cpu_lin_mod = cpumodel.modules[2].modules[i]
--  local gpu_lin_mod = gpumodel.modules[2].modules[i]
--  local w  = gpu_lin_mod.weight
--  local b  = gpu_lin_mod.bias
--  local gw = gpu_lin_mod.gradWeight
--  local gb = gpu_lin_mod.gradBias
--  print('processing linear ..'..tostring(i))
--  cpu_lin_mod.weight = torch.CudaTensor(w:size()):copy(w)
--  cpu_lin_mod.bias = torch.CudaTensor(b:size()):copy(b)
--  cpu_lin_mod.gradWeight = torch.CudaTensor(gw:size()):copy(gw)
--  cpu_lin_mod.gradBias = torch.CudaTensor(gb:size()):copy(gb)
--end

torch.save(cpumodel_path,cpumodel)
