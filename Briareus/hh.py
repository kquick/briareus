#! /usr/bin/env nix-shell
#! nix-shell -i "python3.7 -u" -p git swiProlog "python37.withPackages(pp: with pp; [ thespian setproctitle attrs requests ])"

import Briareus.AnaRep.Operations as AnaRep
from Briareus.AnaRep.Prior import ( get_prior_report, write_report_output )
import Briareus.BCGen.Operations as BCGen
from Briareus.BCGen.Generator import BuildConfigGenTy
import Briareus.Input.Operations as BInput
from Briareus.Input.Description import RepoLoc
from Briareus.BuildSys.BuilderBase import BuilderURL
import Briareus.BuildSys.Hydra as BldSys
import Briareus.Actions.Ops as Actions
from Briareus.Logic.Evaluation import FactList
from Briareus.VCS.ManagedRepo import get_updated_file
from Briareus.VCS_API import UserURL
from Briareus.Types import SendEmail, UpTo
from Briareus.State import RunContext, ReportType, ResultSet
from Briareus.AtomicUpdWriter import FileWriterSession
import argparse
import datetime
import os
import os.path
import sys
from thespian.actors import ActorSystem
import attr
from typing import Any, Callable, Dict, IO, Optional, Sequence, Tuple, Union


@attr.s(auto_attribs=True)
class InpConfig(object):
    hhd: Optional[str] = attr.ib(default=None) # None to read from stdin, else filepath
    input_url: Optional[UserURL] = attr.ib(default=None)  # To fetch Briareus specifications
    input_path: Optional[str] = attr.ib(default=None)     # path under input_url where found
    builder_type: str = attr.ib(default="")
    builder_conf: Optional[str] = attr.ib(default=None)   # builder configuration file
    builder_url: Optional[BuilderURL] = attr.ib(default=None)  # URL for builder results
    output_file: Optional[str] = attr.ib(default=None)    # output filepath (None is stdout)

    def fixup(self) -> "InpConfig":
        expand_filerefs = lambda v: os.path.normpath(os.path.expanduser(os.path.expandvars(v)))
        self.hhd = expand_filerefs(self.hhd)
        self.builder_conf = expand_filerefs(self.builder_conf) \
            if self.builder_conf is not None else None
        self.output_file = expand_filerefs(self.output_file)
        return self


class TimeReporter(object):
    def __init__(self, report: bool = True, phase: str = 'startup') -> None:
        self.report = report
        self.phase = phase
        self.first_start = datetime.datetime.now()
        self.start = self.first_start
    def _report(self) -> None:
        if self.report:
            print('#T:', str(datetime.datetime.now()-self.start), '::',
                  self.phase,
                  file=sys.stderr, flush=True)
    def __call__(self, next_phase: str) -> None:
        self._report()
        self.phase = next_phase
        self.start = datetime.datetime.now()
    def finished(self) -> None:
        self._report()
        self.start = self.first_start
        self.phase = 'Total runtime'
        self._report()
        self.phase = "finished"


@attr.s(auto_attribs=True)
class Params(object):
    verbose: bool = attr.ib(default=False)
    timing_info: TimeReporter = attr.ib(default=TimeReporter(False))
    up_to: Optional["UpTo"] = attr.ib(default=None)  # class UpTo
    report_file: Optional[str] = attr.ib(default=None)
    tempdir: Optional[str] = attr.ib(default=None)


def verbosely(params: Params, *msgargs) -> None:
    if params.verbose:
        print(*msgargs)

# ----------------------------------------------------------------------
# Actual generation and reporting functions

RunHHGenRetTy = Union[Tuple[RunContext, BCGen.BuilderConfigsTy],
                      Union[BuildConfigGenTy,
                            Tuple[BCGen.BuilderConfigsTy, BCGen.GeneratedConfigs]],  # up-to = build_configs
                      RunContext,  # up-to = builder_configs
                      FactList]  # up-to = facts

def run_hh_gen(params: Params,
               inpcfg: InpConfig,
               inp: str,
               bldcfg_fname: str,
               prev_gen_result: RunContext = None) -> RunHHGenRetTy:
    verbosely(params, 'Generating Build Configurations from %s' % inpcfg.hhd)
    if not prev_gen_result:
        params.timing_info('Initializing Run Context and Actors')
    result = (prev_gen_result or
              RunContext(actor_system=ActorSystem('multiprocTCPBase')))
    if inpcfg.builder_type == 'hydra':
        builder = BldSys.HydraBuilder(inpcfg.builder_conf,
                                      builder_url=inpcfg.builder_url)
    else:
        raise RuntimeError('Unknown builder (known: %s), specified: %s' %
                           (', '.join(['hydra']), inpcfg.builder_type))

    params.timing_info('Reading project configuration and VCS info (%s)' % inpcfg.hhd)
    inp_desc, repo_info = \
        BInput.input_desc_and_VCS_info(inp,
                                       verbose=params.verbose,
                                       actor_system=result.actor_system)

    params.timing_info('Generating build configurations (%s)' % inp_desc.PNAME)
    bcgen = BCGen.BCGen(builder,
                        verbose=params.verbose,
                        up_to=params.up_to,
                        actor_system=result.actor_system)
    config_results = bcgen.generate(inp_desc, repo_info,
                                    bldcfg_fname=bldcfg_fname)
    if params.up_to and not params.up_to.enough('builder_configs'):
        return config_results
    assert isinstance(config_results, tuple)
    # assert isinstance(config_results[0], dict) # BuildSys.BuilderConfigsTy
    # assert isinstance(config_results[1], BCGen.GeneratedConfigs)

    builder_cfgs, build_cfgs = config_results
    # builder_cfgs : dictionary of builder configuration file(s),
    #                including the configuration for each build.
    # build_cfgs : Generator.GeneratedConfigs

    result.add_results(builder, inp_desc, repo_info, build_cfgs)

    if params.up_to == 'builder_configs':
        return result

    return result, builder_cfgs


def run_hh_report(params: Params,
                  gen_result: RunContext,
                  prior_report,
                  reporting_logic_defs: str = ''):
    verbosely(params, 'Generating Analysis/Report')
    anarep = AnaRep.AnaRep(verbose=params.verbose,
                           up_to=params.up_to,
                           actor_system=gen_result.actor_system)
    ret = anarep.report_on(gen_result, prior_report,
                           reporting_logic_defs=reporting_logic_defs)

    if ret[0] != 'report':
        return None

    verbosely(params, 'Generated Analysis/Report: %d items' %
              (len(ret[1].report) if isinstance(ret[1], RunContext) else 0))

    return ret[1]


def perform_hh_actions(inpcfg: InpConfig,
                       inp_report: ReportType,
                       run_context: RunContext,
                       report_supplement: Dict[str, Any]):
    run_context.report = [ Actions.do_action(each, inp_report, run_context,
                                             report_supplement)
                           for each in run_context.report ]
    return run_context

# ----------------------------------------------------------------------

def run_hh_gen_with_files(inp: str,
                          inpcfg: InpConfig,
                          outputfname: str,
                          params: Params,
                          prev_gen_result: RunContext = None) -> Optional[RunHHGenRetTy]:
    r = run_hh_gen(params, inpcfg, inp,
                   bldcfg_fname=outputfname,
                   prev_gen_result=prev_gen_result)
    if r is None:
        # Probably an --up-to prevented the full generation
        return None
    if params.up_to and not params.up_to.enough('builder_configs'):
        return None
    return r


def run_hh_gen_on_inpfile(inp_fname: str,
                          params: Params,
                          inpcfg: InpConfig,
                          prev_gen_result: RunContext = None) -> Optional[Union[RunHHGenRetTy,RunContext]]:
    inp_parts = os.path.split(inp_fname)
    outfname = (inpcfg.output_file or
                os.path.join(os.getcwd(),
                             os.path.splitext(inp_parts[-1])[0] + '.hhc'))
    with open(inp_fname) as inpf:
        r = run_hh_gen_with_files(inpf.read(), inpcfg, outfname,
                                  params=params,
                                  prev_gen_result=prev_gen_result)

    if r is None:
        # If r is None, then an --up-to probably halted production
        verbosely(params, 'hh partial run, no output')
        return None

    if params.up_to and not params.up_to.enough('write_bldcfgs'):
        verbosely(params, 'hh partial run, no output')
        return r

    verbosely(params, 'hh <',inp_fname,'>',outfname)
    params.timing_info('Writing outputs (%s)' % outfname)
    writings = FileWriterSession(params.tempdir or os.path.dirname(outfname))

    assert isinstance(r, tuple)  # Tuple[RunContext, BuildSys.BuilderConfigsTy]
    assert isinstance(r[1], dict)  # BuildSys.BuilderConfigsTy
    bldrcfgs = r[1]
    for fname in bldrcfgs:
        if fname:
            assert isinstance(inpcfg.output_file, str)
            indir = os.path.dirname(inpcfg.output_file) or os.getcwd()
            target = fname if fname.startswith(indir) else os.path.join(indir, fname)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            writings.add_file(
                target,
                lambda of: of.write(bldrcfgs[fname]))
        else:
            writings.add_file(
                outfname,
                lambda of: of.write(bldrcfgs[fname]))
    writings.end_session()

    return r[0]


def upd_from_remote(src_url: UserURL,         # URL to fetch update from
                    src_path: Optional[str],  # path underneath url
                    fname: Optional[str],     # Output filename
                    repolocs: Sequence[RepoLoc],
                    actor_system=None) -> None:
    if fname is None: return
    fpath = os.path.join(src_path, os.path.basename(fname)) if src_path else fname
    try:
        data = get_updated_file(src_url, fpath, repolocs, 'master', actor_system=actor_system)
        if data.error_code:
            raise RuntimeError('Error %s' % data.error_code)
    except Exception as ex:
        print('Warning: no remote update of %s from %s: %s'
              % (fpath, src_url, str(ex)),
              file=sys.stderr)
    else:
        if data.file_data:
            try:
                dirname = os.path.dirname(fname)
                if dirname:
                    os.makedirs(dirname, exist_ok=True)
                atomic_write_to(fname, lambda f: f.write(data.file_data))
            except Exception as ex:
                print('Warning: failed writing to %s: %s  [contents: %s]'
                      % (fname, str(ex), str(data)),
                      file=sys.stderr)
        else:
            print('No contents obtained for %s @ %s'
                  % (fpath, src_url))


def run_hh_on_inpcfg(inpcfg: InpConfig,
                     params: Params,
                     prev_gen_result: RunContext = None) -> Optional[Union[RunHHGenRetTy,RunContext]]:
    if inpcfg.input_url is not None:
        params.timing_info('Updating inputs from %s' % inpcfg.input_url)
        asys = ((prev_gen_result.actor_system if prev_gen_result else None)
                or ActorSystem('multiprocTCPBase'))
        try:
            upd_from_remote(inpcfg.input_url, inpcfg.input_path, inpcfg.hhd, [], asys)
            upd_from_remote(inpcfg.input_url, inpcfg.input_path, inpcfg.builder_conf, [], asys)
        except:
            print('Warning: update from remote %s path %s failed (%s, %s)' %
                  (inpcfg.input_url, inpcfg.input_path, inpcfg.hhd, inpcfg.builder_conf))
    ifile = (inpcfg.hhd
             if inpcfg.hhd is not None and os.path.exists(inpcfg.hhd)
             else ((inpcfg.hhd + '.hhd')
                   if inpcfg.hhd is not None and os.path.exists(inpcfg.hhd + '.hhd')
                   else None))
    if not ifile:
        raise RuntimeError('Input specification not found (in %s): %s' %
                           (os.getcwd(), inpcfg.hhd))
    return run_hh_gen_on_inpfile(ifile, params=params, inpcfg=inpcfg, prev_gen_result=prev_gen_result)


def read_inpcfgs_from(inputArg: Optional[str]) -> Dict[str, Any]:
    """Reads the -C input configuration file.  The format is a python
       dictionary, with keys of 'InpConfigs' (value is a list of
       InpConfig objects) and 'Reporting' which is a dictionary with
       sub-keys 'logic', whose value is a string specifying additional
       logic statements to express during the reporting phase
       (e.g. email_whitelist_domain, etc.).

    """
    if inputArg is None:
        inp = input('Briareus input configurations? ')
    else:
        with open(inputArg) as inpf:
            inp = inpf.read()
    # A parser we already have, although it's dangerous...
    inpParsed = eval(inp.strip())
    inpParsed['InpConfigs'] = [ each.fixup() for each in inpParsed['InpConfigs'] ]
    return inpParsed


def run_hh_reporting_to(reportf,
                        params: Params,
                        inputArg=None,
                        inpcfg: Optional[InpConfig] = None,
                        prior_report=None) -> None:
    """Runs the Briareus operation, writing the output to reportf if not
       None. If inpcfg is set, then this is for that single
       configuration, otherwise the input configurations are read from
       inputArg (stdin if inputArg is None).

    """
    if inpcfg is None:
        params.timing_info('Reading input configurations')
        inpcfgs = read_inpcfgs_from(inputArg)
        if not inpcfgs:
            raise ValueError('No input configurations specified')
        gen_result = None
        for inpcfg in inpcfgs['InpConfigs']:
            gen_result = run_hh_on_inpcfg(inpcfg, params, prev_gen_result=gen_result)
        report_supplement = inpcfgs.get('Reporting', dict())
    else:
        gen_result = run_hh_on_inpcfg(inpcfg, params)
        report_supplement = dict()

    # Generator cycle done, now do any reporting

    if params.up_to and not params.up_to.enough('build_results'):
        return

    if reportf or (params.up_to and params.up_to.enough('built_facts')):

        params.timing_info('Generating report')
        assert isinstance(gen_result, RunContext)
        upd_result = run_hh_report(params, gen_result, prior_report,
                                   reporting_logic_defs=(report_supplement
                                                         .get('logic', '')))

        if params.up_to and not params.up_to.enough('actions'):
            return

        params.timing_info('Performing Actions')
        act_result = perform_hh_actions(inpcfg, upd_result.report, upd_result,
                                        report_supplement)

        if reportf and (not params.up_to or params.up_to.enough('report')):
            params.timing_info('Writing final report')
            write_report_output(reportf, act_result.report)


def atomic_write_to(outfname: str,
                    gen_output: Callable[[IO], Optional[int]]) -> Optional[int]:
    tryout = os.path.join(os.path.dirname(outfname),
                          '.' + os.path.basename(outfname) + '.new')
    with open(tryout, 'w') as outf:
        r = gen_output(outf)
    os.rename(tryout, outfname)
    return r


def run_hh(params: Params, inpcfg: Optional[InpConfig] = None, inputArg=None):
    verbosely(params, 'Running hh')
    if inpcfg is None:
        verbosely(params, 'multiple input configs from:', inputArg)
    else:
        verbosely(params, 'input from:', inpcfg.hhd)
    if params.report_file and (not params.up_to or params.up_to.enough('built_facts')):
        verbosely(params, 'Reporting to', params.report_file)
        params.timing_info('Reading prior report (%s)' % params.report_file)
        prior_rep_fd, prior_report = get_prior_report(params.report_file)
        # n.b. the rep_fd references the locked file descriptor; keep
        # this reference to keep the lock active and prevent
        # simultaneous Briareus runs from colliding.
        atomic_write_to(
            params.report_file,
            lambda rep_fd: run_hh_reporting_to(rep_fd, params,
                                               inputArg=inputArg,
                                               inpcfg=inpcfg,
                                               prior_report=prior_report))
    else:
        verbosely(params, 'No reporting')
        run_hh_reporting_to(None, params, inputArg=inputArg, inpcfg=inpcfg)
    verbosely(params,'hh',('completed up to: ' + str(params.up_to))
              if params.up_to else 'done')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Run the Briareus (the Hundred Hander) tool to generate build configurations.',
        epilog=('The BRIAREUS_PAT environment variable can be used to supply "repo=token;..." '
                'specifications of access tokens needed for access to the specified repo.'),
        prog='hh')
    parser.add_argument(
        '--report', '-r', default=None,
        help=('Output file for writing build reports.  Also read as '
              'input for generating a report relative to previous reporting. '
              'The default is {inputfile}.hhr or stdout if no inputfile.'))
    parser.add_argument(
        '--builder', '-b', default='hydra',
        help=('Backend builder to generate build configurations for.  Valid builders '
              'are: hydra.  The default is to use the %(default)s builder backend.'))
    parser.add_argument(
        '--builder-config', '-B', default=None, dest="builder_conf",
        help="Configuration file for backend builder")
    parser.add_argument(
        '--builder-url', '-U', default=None, dest="builder_url",
        help="""URL of builder to obtain build results.  If not specified, no build
                results will be available for reporting.""")
    parser.add_argument(
        '--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument(
        '--timing-info', '-T', action='store_true', dest="timing_info",
        help='Display timing information to stderr from sub-segments of'
        ' execution.')
    parser.add_argument(
        '--up-to', '-u', default=None, dest="up_to", type=UpTo,
        help='''For debugging: run hh up to the designated point and stop, printing
                the results to stdout (ignoring the -o argument).
                Valid ending points: %s''' % UpTo.valid())
    parser.add_argument(
        '--stop-daemon', '-S', dest="stopdaemon", action='store_true',
        help='''Stop daemon processes on exit.  Normally Briareus leaves daemon
                processes running that can be used on subsequent runs
                to perform GitHub queries (knowledge of previous
                results helps stay below GitHub request limits).  This
                flag causes those processes to be shutdown on exit
                (even if running from a previously issued command.''')
    parser.add_argument(
        '--cfg-input', '-C', dest='cfginput', action='store_true',
        help='''Input file specifies a python list of InpConfig values describing
                multiple projects to process.  This flag is
                incompatible with the -U, -B, -b, -I, and -o
                flags, and changes the interpretation of the input
                file from a single Briareus input specification to a
                list of InpConfig structures, each describing a
                Briareus project.  This mode is used when the Analysis
                and Reporting (AnaRep) phase should consider the
                results of all projects instead of just a single
                project.''')
    parser.add_argument(
        '--tempdir',
        help='''Specify a temporary directory to use when generating new files.
                Output files will initially be created in this
                location and then moved to the actual destination if
                the file is newer.  The default is to use the output
                directory for the temporary files.  Note that if
                specified, the tempdir should be on the same
                filesystem''')
    parser.add_argument(
        '--input-url-and-path', '-I',
        help='''Specify an input URL from which the INPUT files (and
                builder-config, if specified) should be updated
                from. The value should be a "url+path" with an actual
                plus sign; the INPUT and builder-config files should
                exist in the "path" location at the "url".

                This is done atomically, so any existing files are not
                overwritten if the update fails; normal Briareus
                action continues even if this update is unsuccessful.

                This is particularly useful if the INPUT and
                builder-config files are contained in a private remote
                repository for which the BRIAREUS_PAT provides access
                tokens for updates.''')
    parser.add_argument(
        'INPUT',
        help='Briareus input specification (file or URL)')
    parser.add_argument(
        'OUTPUT', nargs='?', default=None,
        help=('Output file for writing build configurations.'
              'The default is {inputfile}.hhc.'))
    args = parser.parse_args()
    params = Params(verbose=args.verbose,
                    timing_info=TimeReporter(report=args.timing_info),
                    up_to=args.up_to,
                    report_file=args.report,
                    tempdir=args.tempdir)
    if args.cfginput:
        if args.builder_url or args.builder_conf or \
           args.input_url_and_path or args.OUTPUT:
            raise ValueError('Cannot use -C with any of: -U, -B, -b, -I, or OUTPUT')
        inpcfg = None
        inputArg = args.INPUT
    else:
        input_url, input_path = args.input_url_and_path.split('+') if args.input_url_and_path else (None,None)
        inpcfg = InpConfig(hhd=args.INPUT,
                           input_url=UserURL(input_url) if input_url else None,
                           input_path=input_path,
                           builder_type=args.builder,
                           builder_conf=args.builder_conf,
                           builder_url=BuilderURL(args.builder_url),
                           output_file=args.OUTPUT or
                           (os.path.splitext(args.INPUT)[0] + ".hhc"))
        inputArg = None

    try:
        run_hh(params, inpcfg=inpcfg, inputArg=inputArg)
    finally:
        params.timing_info.finished()
        if args.stopdaemon:
            ActorSystem().shutdown()

if __name__ == "__main__":
    main()
