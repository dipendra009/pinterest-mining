--
--  Copyright (c) 2014, Facebook, Inc.
--  All rights reserved.
--
--  This source code is licensed under the BSD-style license found in the
--  LICENSE file in the root directory of this source tree. An additional grant
--  of patent rights can be found in the PATENTS file in the same directory.
--
require 'torch'
require 'cutorch'
require 'paths'
require 'xlua'
require 'optim'
require 'nn'

local opts = paths.dofile('opts.lua')
opt = opts.parse(arg)

if opt.backend ~= 'fbcunn' then --if fbcunn backend is chosen, these files will be imported from `require 'fbcunn'`
	paths.dofile('fbcunn_files/AbstractParallel.lua')
	paths.dofile('fbcunn_files/ModelParallel.lua')
	paths.dofile('fbcunn_files/DataParallel.lua')
	paths.dofile('fbcunn_files/Optim.lua')
end
print(opt)
--os.execute("rm " .. paths.concat(opt.cache, '*.t7'))
torch.setdefaulttensortype('torch.FloatTensor')

cutorch.setDevice(opt.GPU) -- by default, use GPU 1
torch.manualSeed(opt.manualSeed)

print('Saving everything to: ' .. opt.save)
os.execute('mkdir -p ' .. opt.save)

paths.dofile('data.lua')
paths.dofile('model.lua')
paths.dofile('vertical_feat.lua')
paths.dofile('util.lua')

epoch = opt.epochNumber
assert(opt.retrain, "Only works with an already trained model.")
test(opt.ClassesVertical1)
