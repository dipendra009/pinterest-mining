--
--  Copyright (c) 2014, Facebook, Inc.
--  All rights reserved.
--
--  This source code is licensed under the BSD-style license found in the
--  LICENSE file in the root directory of this source tree. An additional grant
--  of patent rights can be found in the PATENTS file in the same directory.
--
require 'nn'
require 'cunn'
require 'optim'
require 'cudnn'
--[[
   1. Create Model
   2. Create Criterion
   3. If preloading option is set, preload weights from existing models appropriately
   4. Convert model to CUDA
]]--

-- 1.1. Create Network

-- 2. Create Criterion
criterion = nn.ClassNLLCriterion()


-- 3. If preloading option is set, preload weights from existing models appropriately
if opt.usemodel ~= 'none' then
    assert(paths.filep(opt.usemodel), 'File not found: ' .. opt.usemodel)
    print('Loading model from file: ' .. opt.usemodel);
    model = torch.load(opt.usemodel)
end

-- 4. Convert model to CUDA
print('==> Converting model to CUDA')
model = model:cuda()
criterion:cuda()

collectgarbage()
