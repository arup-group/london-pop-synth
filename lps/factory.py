from lps import loham, lopops, motion, momo
from lps.loham.config import LoHAMLGVConfig, LoHAMHGVConfig
from lps.lopops.config import LoPopSConfig
from lps.motion.config import MotionConfig
from lps.momo.config import MoMoConfig
from lps.core import samplers


synth_map = {
    'loham_lgv':
        {
            'config': LoHAMLGVConfig,
            'input': loham.Demand,
            'sampler': samplers.DemandSampler,
         },
    'loham_hgv':
        {
            'config': LoHAMHGVConfig,
            'input': loham.loham.Demand,
            'sampler': samplers.DemandSampler,
         },
    'lopops':
        {
            'config': LoPopSConfig,
            'input': lopops.lopops.Data,
            'sampler': samplers.ObjectSampler,
        },
    'motion':
        {
            'config': MotionConfig,
            'input': motion.motion.Demand,
            'sampler': samplers.DemandSampler,
        },
    'momo':
        {
            'config': MoMoConfig,
            'input': momo.momo.Data,
            'sampler': samplers.NotRequired,
        }
}