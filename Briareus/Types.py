# Data representation of build configurations and report data
#
# ALL Logic output items are translated back into Python objects and
# values defined here via the logic_result_expr translation below.

import attr
from Briareus.Input.Description import InputDesc
from Briareus.BuildSys_API import BuilderURL
from typing import (Any, Dict, Hashable, List, Optional, Sequence, Union)

def sorted_nub_list(l: Sequence[Hashable]) -> List[Hashable]:
    return sorted(list(set(l)))


@attr.s(auto_attribs=True, frozen=True)
class BranchReq(object):
    projectname: str
    branchname: str

    def as_fact(self) -> str:
        return 'branchreq("' + self.projectname + '", "' + self.branchname + '")'


@attr.s(auto_attribs=True, frozen=True)
class MainBranch(object):
    reponame: str
    branchname: str

    def as_fact(self) -> str:
        return 'main_branch("' + self.reponame + '", "' + self.branchname + '")'

def pr_type(typespec, *args):
    return eval(typespec)(*args)

@attr.s(auto_attribs=True, frozen=True)
class PR_Solo(object):
    projectname: str
    reponame: str
    pullreq_id: str # never project_primary

    def as_fact(self) -> str:
        return ('pr_type(pr_solo, "' + self.projectname +
                '", "' + self.reponame +
                '", "' + self.pullreq_id + '")')

@attr.s(auto_attribs=True, frozen=True)
class PR_Repogroup(object):
    projectname: str
    pullreq_id: str  # never project_primary
    reponames: List[str]

    def as_fact(self) -> str:
        return ('pr_type(pr_repogroup, "' + self.projectname +
                '", "' + self.pullreq_id +
                '", ['
                + ', '.join(['"%s"'%n for n in self.reponames]) + '])')

@attr.s(auto_attribs=True, frozen=True)
class PR_Grouped(object):
    branchname: str

    def as_fact(self) -> str:
        return 'pr_type(pr_grouped, "' + self.branchname + '")'

@attr.s(auto_attribs=True, frozen=True)
class BldRepoRev(object):
    reponame: str
    repover: str
    pullreq_id: str  # project_primary or the PR ID
      # srcident identifies the source loc in the Logic rules and is
      # used for debugging the ruleset.  As a result, it is ignored
      # for comparisons since a specific repo revision build
      # instruction is effective in the builder regardless of which
      # logic statement generated it.
    srcident: str = attr.ib(default="unk", eq=False)

@attr.s(auto_attribs=True, frozen=True)
class BldVariable(object):
    project: str
    varname: str
    varvalue: str


BldDescTy = Union["PR_Solo", "PR_Repogroup", "PR_Grouped",
                  "BranchReq", "MainBranch", str]


@attr.s(auto_attribs=True, frozen=True)
class BldConfig(object):
    projectname: str
    branchtype: str  # default="regular"
    branchname: str
    strategy: str   # default="standard"
    description: BldDescTy
    blds: List["BldRepoRev"] = attr.ib(factory=list, converter=sorted_nub_list)
    bldvars: List[BldVariable] = attr.ib(factory=list, converter=sorted_nub_list)


# ----------------------------------------------------------------------

@attr.s(auto_attribs=True, frozen=True)
class BuildResult(object):
    bldconfig: BldConfig
    results: Union[str, "BuilderResult"]

@attr.s(auto_attribs=True, frozen=True)
class BuilderResult(object):
    buildname: str  # string name of build on builder
    nrtotal: int
    nrsucceeded: int
    nrfailed: int
    nrscheduled: int
    cfgerror: bool
    builder_url: Optional[BuilderURL]


# ----------------------------------------------------------------------
# Reporting

@attr.s(auto_attribs=True, frozen=True)
class ProjectSummary(object):
    project_name: str
    bldcfg_count: int
    subrepo_count: int
    pullreq_count: int

@attr.s(auto_attribs=True, frozen=True)
class StatusReport(object):
    status: Union[str, int]  # string "succeeded", "fixed", "initial_success", "pending", "badconfig", or int count of failing build jobs.
    project: str     # name of project
    strategy: str    # submodules, heads, standard
    branchtype: str  # regular, pullreq
    branch: str      # branch name
    buildname: str   # name of build on builder
    bldvars: List[BldVariable] = attr.ib(converter=sorted)
    blddesc: BldDescTy = attr.ib(default="unk")  # same as BldConfig.description above

@attr.s(auto_attribs=True, frozen=True)
class PendingStatus(object):
    """Just like StatusReport, but no 'status' field because there will
       (maybe) be a StatusReport from a previous build and this
       indicates there is a new build in progress.
    """
    project: str     # name of project
    strategy: str    # submodules, heads, standard
    branchtype: str  # regular, pullreq
    branch: str      # branch name
    buildname: str   # name of build on builder
    bldvars: List[BldVariable] = attr.ib(converter=sorted)
    blddesc: BldDescTy = attr.ib(default="unk")  # same as BldConfig.description above

@attr.s(auto_attribs=True, frozen=True)
class NewPending(object):
    bldcfg: BldConfig

@attr.s(auto_attribs=True, frozen=True)
class VarFailure(BldVariable): pass

@attr.s(auto_attribs=True, frozen=True)
class PR_Status(object):
    prtype: Union[PR_Solo, PR_Repogroup, PR_Grouped]
    branch: str
    project: str
    strategy: str  # submodules, heads, standard
    prcfg: List[Union["PRCfg", "BranchCfg"]]
    prstatus_blds: "PR_Status_Blds"

@attr.s(auto_attribs=True, frozen=True)
class PR_Status_Blds(object):
    passing: List[str]  # list of passing BldNames
    failing: List[str]  # list of failing BldNames
    pending: List[str]  # list of pending BldNames (i.e. in-progress)
    unstarted: int      # number of builds not yet started

fact_str = lambda s: '"' + s + '"'
fact_list = lambda l: '[' + ', '.join([e.as_fact() if hasattr(e, 'as_fact') else fact_str(e)
                                       for e in l]) + ']'

@attr.s(auto_attribs=True, frozen=True)
class PRCfg(object):
    reponame: str
    pr_id: str
    branch: str
    revision: str # head revision (e.g. SHA hash) or blank if not known
    user: str
    email: str

    def as_fact(self) -> str:
        return ''.join(['prcfg(',
                        ','.join([
                            fact_str(self.reponame),
                            fact_str(self.pr_id),
                            fact_str(self.branch),
                            fact_str(self.revision),
                            fact_str(self.user),
                            fact_str(self.email),
                            ]),
                        ')'])

@attr.s(auto_attribs=True, frozen=True)
class BranchCfg(object):
    reponame: str
    branch: str

    def as_fact(self) -> str:
        return ''.join(['branchcfg(',
                        fact_str(self.reponame), ',',
                        fact_str(self.branch),
                        ')'])

@attr.s(auto_attribs=True, frozen=True)
class PRData(object):
    prtype: Union[PR_Solo, PR_Repogroup, PR_Grouped]
    prcfg: List[Union[PRCfg, BranchCfg]]

    def as_fact(self) -> str:
        return ''.join(['prdata(',
                        self._as_fact_fields(),
                        ')'])

    def _as_fact_fields(self) -> str:
        return ', '.join([self.prtype.as_fact(),
                          fact_list(self.prcfg),
        ])

@attr.s(auto_attribs=True, frozen=True)
class BldSet(object):
    brtype: str    # "pullreq" or "regular"
    strategy: str  # "submodules", "heads" or "regular"
    goods: List[str] = attr.ib(converter=sorted) # list of BuildNames
    fails: List[str] = attr.ib(converter=sorted) # list of BuildNames

    def as_fact(self) -> str:
        return ('bldset(' +
                ', '.join([self.brtype,
                           self.strategy,
                           fact_list(self.goods),
                           fact_list(self.fails),
                ]) +
                ')')

@attr.s(auto_attribs=True, frozen=True)
class PRFailedSubBlds(PRData):
    pr_subs: BldSet    # BldSet for pullreq submodules
    pr_heads: BldSet   # BldSet for pullreq heads
    main_heads: BldSet # BldSet for main branch heads
    main_subs: BldSet  # BldSet for main branch submodules

    def as_fact(self) -> str:
        return ('prfailedblds(' +
                ', '.join([super()._as_fact_fields(),
                           self.pr_subs.as_fact(),
                           self.pr_heads.as_fact(),
                           self.main_heads.as_fact(),
                           self.main_subs.as_fact(),
                ]) +
                ')')

@attr.s(auto_attribs=True, frozen=True)
class PRFailedStdBlds(PRData):
    pr_blds: BldSet    # BldSet for pullreq standard
    main_blds: BldSet  # BldSet for main branch standard

    def as_fact(self) -> str:
        return ('prfailedblds(' +
                ', '.join([super()._as_fact_fields(),
                           self.pr_blds.as_fact(),
                           self.main_blds.as_fact(),
                ]) +
                ')')

def pr_failedblds(*args) -> Union[PRFailedStdBlds, PRFailedSubBlds]:
    if len(args) == 4:
        return PRFailedStdBlds(*args)
    elif len(args) == 6:
        return PRFailedSubBlds(*args)
    else:
        raise IndexError('pr_faildblds with %d args not implemented' % len(args))

@attr.s(auto_attribs=True, frozen=True)
class CompletelyFailing(object):
    project: str # name of project

# ----------------------------------------------------------------------
# Analysis

@attr.s(auto_attribs=True, frozen=True)
class SepHandledVar(object):
    project: str   # project repo
    var_name: str  # variable name
    var_value: str # variable value

# ----------------------------------------------------------------------
# Actions

@attr.s(auto_attribs=True, frozen=True)
class Notify(object):
    what: str         # type of notification
    subject: str      # project
    params: Union[PRData, List[Any]] # parameters associated with item; specific to 'what'


@attr.s(auto_attribs=True, frozen=True)
class SendEmail(object):
    recipients: List[str] = attr.ib(converter=sorted_nub_list) # list of email addresses
    notification: Notify
    sent_to: List[str] = attr.ib(converter=sorted_nub_list) # list of addresses message has been sent to already

@attr.s(auto_attribs=True, frozen=True)
class PostChatMessage(object):
    channels: List[str]  # list of channels
    what: Notify         # Notification type
    posted: List[str]    # list of channels message has been posted to already

@attr.s(auto_attribs=True, frozen=True)
class SetForgeStatus(object):
    targetrepos: List[str] = attr.ib(converter=sorted_nub_list) # list of repo names
    notification: Notify
    updated: List[str] = attr.ib(converter=sorted_nub_list) # list of repo names posting has been made to

# ----------------------------------------------------------------------
# The Prolog output is currently interpreted via an "eval({output})"
# operation, so define some terms to re-ify the eval'd string into
# Python description.

logic_result_expr = {
    "pullreq": "pullreq",
    "submodules": "submodules",
    "heads": "HEADs",
    "regular": "regular",
    "standard": "standard",
    "project_primary": "project_primary",
    "bldcfg": lambda *args: BldConfig(*args),
    "branchreq": BranchReq,
    "main_branch": MainBranch,
    "pr_type": pr_type,
    "pr_solo": "PR_Solo",
    "pr_repogroup": "PR_Repogroup",
    "pr_grouped": "PR_Grouped",
    "bld": lambda *args: BldRepoRev(*args),
    "brr": lambda n: n,
    "varvalue": lambda *args: BldVariable(*args),

    "status_report": StatusReport,
    "pending_status": PendingStatus,
    "new_pending": NewPending,
    "succeeded": "succeeded",
    "failed": "failed",
    "fixed": "fixed",
    "initial_success": "initial_success",
    "badconfig": "bad_config",
    "bad_config": "bad_config",
    "pending": "pending",
    "var_failure": lambda *args: VarFailure(*args),
    "pr_status": PR_Status,
    "pr_status_blds": PR_Status_Blds,
    "prcfg": PRCfg,
    "branchcfg": BranchCfg,
    "pr_projstatus_pending": "pr_projstatus_pending",
    "pr_projstatus_good": "pr_projstatus_good",
    "pr_projstatus_fail": "pr_projstatus_fail",
    "prdata": PRData,
    "prfailedblds": pr_failedblds,
    "bldset": BldSet,
    "complete_failure": lambda *args: CompletelyFailing(*args),

    "var_handled_separately": lambda *args: SepHandledVar(*args),

    "notify": lambda *args: Notify(*args),
    "email": lambda *args: SendEmail(*args),
    "chat": lambda *args: PostChatMessage(*args),
    "set_forge_status": SetForgeStatus,
    "merge_pr": "merge_pr",
    "completely_broken": "completely_broken",
    "main_submodules_broken": "main_submodules_broken",
    "main_submodules_good": "main_submodules_good",
    "main_good": "main_good",
    "main_broken": "main_broken",
    "variable_failing": "variable_failing",


    "project": lambda n: n,
}


class UpTo(object):
    """Specifies an endpoint for the processing (for debugging or
       informational purposes).  Note that this object does not encode
       a "no restrictions" value; None should be used instead of this
       object for an unrestricted execution.
    """

    # In order:
    valid_up_to = [ "facts", "raw_logic_output", "build_configs", "builder_configs",
                    "write_bldcfgs",
                    "build_results", "built_facts", "raw_built_analysis",
                    "actions", "report" ]

    @staticmethod
    def valid() -> str:
        return ', '.join(UpTo.valid_up_to)

    def __init__(self, arg: str) -> None:
        if arg not in UpTo.valid_up_to:
            raise ValueError("The --up-to value must be one of: " + self.valid())
        self._up_to = arg

    def __eq__(self, o: object) -> bool:
        # Compare this object to a string to see if the string matches
        # the internal value. This is usually the indicator for the
        # checker to exit because the termination point has been
        # reached.
        assert isinstance(o, str)
        return self._up_to == o

    def __str__(self) -> str: return self._up_to

    def enough(self, point: str) -> bool:
        """Returns true if the internal up_to value is one of the valid values
           at or after the point value; this indicates that enough
           processing has been performed and the code should simply
           proceed to exit.  If false, more processing was
           requested.
        """
        pt = UpTo.valid_up_to.index(point)  # Throws a ValueError if point is not in the valid list
        return UpTo.valid_up_to.index(self._up_to) >= pt
