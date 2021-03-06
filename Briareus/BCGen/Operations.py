# Briareus BCGen functionality: create Build Configurations from input
# specifications and repository information.

from Briareus import print_each
from Briareus.Types import UpTo
from Briareus.VCS_API import RepoInfoTy
from Briareus.Input.Description import InputDesc
from Briareus.BuildSys.BuilderBase import BuilderConfigsTy, Builder
import Briareus.Input.Parser as Parser
from Briareus.BCGen.Generator import BuildConfigGenTy, GeneratedConfigs, Generator
from typing import Tuple, Union


class BCGen(object):
    def __init__(self, bldsys: Builder,
                 actor_system=None,
                 verbose: bool = False,
                 up_to: UpTo = None) -> None:
        self._bldsys = bldsys
        self._actor_system = actor_system
        self.verbose = verbose
        self._up_to = up_to

    def generate(self, input_desc: InputDesc,
                 repo_info: RepoInfoTy,
                 bldcfg_fname: str = None) -> Union[BuildConfigGenTy,
                                                    Tuple[BuilderConfigsTy,
                                                          GeneratedConfigs]]:
        gen = Generator(actor_system=self._actor_system, verbose=self.verbose)
        (rtype, cfgs) = gen.generate_build_configs(input_desc, repo_info,
                                                   up_to=self._up_to)
        if rtype != "build_configs":   # early up_to abort
            return cfgs
        assert isinstance(cfgs, GeneratedConfigs)
        if self.verbose or self._up_to == "build_configs":
            print_each('BUILD CONFIGS', cfgs.cfg_build_configs)
            print_each('SUBREPOS', cfgs.cfg_subrepos)
            print_each('PULL REQUESTS', cfgs.cfg_pullreqs)
        if self._up_to and not self._up_to.enough("builder_configs"):
            return cfgs
        cfg_spec = self._bldsys.output_build_configurations(input_desc, cfgs,
                                                            bldcfg_fname=bldcfg_fname,
                                                            verbose=self.verbose
        )
        return cfg_spec, cfgs
