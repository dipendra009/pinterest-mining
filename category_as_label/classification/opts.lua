--
--  Copyright (c) 2014, Facebook, Inc.
--  All rights reserved.
--
--  This source code is licensed under the BSD-style license found in the
--  LICENSE file in the root directory of this source tree. An additional grant
--  of patent rights can be found in the PATENTS file in the same directory.
--
local M = { }

function M.parse(arg)
   local defaultDir = paths.concat(os.getenv('HOME'), 'Work/Pinterest/category_as_label')

    local cmd = torch.CmdLine()
    cmd:text()
    cmd:text('Torch-7 Pinterest Training script')
    cmd:text()
    cmd:text('Options:')
    ------------ General options --------------------

    cmd:option('-cache',
               defaultDir..'/model_runs',
               'subdirectory in which to save/log experiments')
    cmd:option('-data',
               '/raid/rll943/PinsByCategory/split_images/',
               'Home of dataset')
    cmd:option('-manualSeed',        12, 'Manually set RNG seed')
    cmd:option('-GPU',                1, 'Default preferred GPU')
    cmd:option('-nGPU',               1, 'Number of GPUs to use by default')
    cmd:option('-backend',     'cudnn', 'Options: cudnn | fbcunn | cunn')
    ------------- Data options ------------------------
    cmd:option('-nDonkeys',        8, 'number of donkeys to initialize (data loading threads)')
    ------------- Training options --------------------
    cmd:option('-samplingMode',    'balanced',   'balanced or random')
    cmd:option('-trainScheme',    'full',   'short training or full training')
    cmd:option('-nEpochs',         60,   'Number of total epochs to run')
    cmd:option('-epochSize',       2500, 'Number of batches per epoch')
    cmd:option('-epochNumber',     1,     'Manual epoch number (useful on restarts)')
    cmd:option('-saveAfter',       60,     'save model after this epoches (instead of saving it every epoch)')
    cmd:option('-batchSize',       128,   'mini-batch size (1 = pure stochastic)')
    cmd:option('-testBatchSize',   8,     'mini-batch size (1 = pure stochastic)')
    ---------- Optimization options ----------------------
    cmd:option('-LR',    0.0, 'learning rate; if set, overrides default LR/WD recipe')
    cmd:option('-momentum',        0.9,  'momentum')
    cmd:option('-weightDecay',     5e-4, 'weight decay')
    ---------- Model options ----------------------------------
    cmd:option('-netType',     'vggbn', 'Options: alexnet | overfeat')
    cmd:option('-retrain',     'none', 'provide path to model to retrain with')
    cmd:option('-usemodel',    'model_60.t7', 'provide path to model to load and use')
    cmd:option('-topXbar',    0.75, 'a threshold to determine x')
    cmd:option('-optimState',  'none', 'provide path to an optimState to reload from')
    cmd:text()

    local opt = cmd:parse(arg or {})
    -- add commandline specified options
    opt.save = paths.concat(opt.cache,
                            cmd:string(opt.netType, opt,
                                       {netType=true, retrain=true, optimState=true, cache=true, data=true}))
    -- add date/time
    local datestr = os.date():gsub('  ',' '):gsub(' ','_')
    opt.save = paths.concat(opt.save, datestr)
    return opt
end

return M
