from Briareus.Types import BldConfig, BldRepoRev, BldVariable, BranchReq, PR_Grouped, MainBranch
from Briareus.VCS_API import (BranchRef, PRSts_Active, PRSts_Merged, PRSts_Closed, PRInfo,
                              RepoInfoTy, RepoSite, SubModuleInfo)
from test_example import expected_repo_info
import json
import pytest

# Different top-level R10 shares R3 and R4 with test_example.py.  This also has different variables.

input_spec = open('test/inp_example3').read()

expected_repo_info = RepoInfoTy(
    info_branches = set([
        BranchRef(reponame='R10', branchname='master', branchref='R10-master-ref'),
        BranchRef(reponame='R3', branchname='blah', branchref='r3-blah-ref'),
        BranchRef(reponame='R3', branchname='master', branchref='R3-master-ref'),
        BranchRef(reponame='R4', branchname='feat1', branchref='r4-feat1-ref'),
        BranchRef(reponame='R4', branchname='master', branchref='R4-master-ref'),
    ]),
    info_pullreqs = set([
        PRInfo(pr_target_repo='R3', pr_srcrepo_url='https://github.com/remote_r3_CLOSED_url', pr_branch='closed_pr',
               pr_revision='r3_CLOSED_mergeref', pr_ident='22', pr_status=PRSts_Closed(),
               pr_title='ignored because closed', pr_user='done', pr_email='done@already.yo'),
        PRInfo(pr_target_repo='R3', pr_srcrepo_url='https://github.com/remote_r3_MERGED_url', pr_branch='merged_pr',
               pr_revision='r3_MERGED_mergeref', pr_ident='33', pr_status=PRSts_Merged(),
               pr_title='ignored because merged', pr_user='done', pr_email='done@already.yo'),
        PRInfo(pr_target_repo='R3', pr_srcrepo_url='https://github.com/remote_r3_pr11_url', pr_branch='blah',
               pr_revision='r3_blah_mergeref', pr_ident='11', pr_status=PRSts_Active(),
               pr_title='blah started', pr_user='nick', pr_email='nick@bad.seeds'),
        PRInfo(pr_target_repo='R4', pr_srcrepo_url='https://github.com/remote_R4_y', pr_branch='bugfix9',
               pr_revision='r4_bf9_mergeref', pr_ident='8192', pr_status=PRSts_Active(),
               pr_title='fix ninth bug!', pr_user='ozzie', pr_email='ozzie@crazy.train'),
    ]),
    info_submodules = set([
        SubModuleInfo(sm_repo_name='R10', sm_branch='master', sm_pullreq_id=None, sm_sub_name='R3', sm_sub_vers='r3_master_head^9'),
        SubModuleInfo(sm_repo_name='R10', sm_branch='master', sm_pullreq_id=None, sm_sub_name='R4', sm_sub_vers='r4_master_head^1'),
    ]),
    info_subrepos = set([
        RepoSite(repo_name='R3', repo_url='https://github.com/r3_url', main_branch='master', use_submodules=False),
        RepoSite(repo_name='R4', repo_url='https://github.com/r4_url', main_branch='master', use_submodules=False),
    ]),
)


expected_facts = sorted(filter(None, '''
:- discontiguous project/1.
:- discontiguous project/2.
:- discontiguous repo/2.
:- discontiguous subrepo/2.
:- discontiguous main_branch/2.
:- discontiguous submodule/5.
:- discontiguous branchreq/2.
:- discontiguous branch/2.
:- discontiguous branch_ref/3.
:- discontiguous pullreq/7.
:- discontiguous varname/2.
:- discontiguous varvalue/4.
project("R10").
project("R10", "R10").
default_main_branch("master").
repo("R10", "R10").
subrepo("R10", "R3").
subrepo("R10", "R4").
branch("R10", "master").
branch("R3", "master").
branch("R3", "blah").
branch("R4", "master").
branch("R4", "feat1").
branch_ref("R10", "master", "R10-master-ref").
branch_ref("R3", "master", "R3-master-ref").
branch_ref("R3", "blah", "r3-blah-ref").
branch_ref("R4", "master", "R4-master-ref").
branch_ref("R4", "feat1", "r4-feat1-ref").
pullreq("R3", "11", "blah", "r3_blah_mergeref", prsts_active, "nick", "nick@bad.seeds").
pullreq("R3", "22", "closed_pr", "r3_CLOSED_mergeref", prsts_closed, "done", "done@already.yo").
pullreq("R3", "33", "merged_pr", "r3_MERGED_mergeref", prsts_merged, "done", "done@already.yo").
pullreq("R4", "8192", "bugfix9", "r4_bf9_mergeref", prsts_active, "ozzie", "ozzie@crazy.train").
branchreq("R10", "master").
branchreq("R10", "dev").
branchreq("R10", "feat1").
submodule("R10", project_primary, "master", "R3", "r3_master_head^9").
submodule("R10", project_primary, "master", "R4", "r4_master_head^1").
varname("R10", "ghcver").
varvalue("R10", "ghcver", "ghc822", 0).
varvalue("R10", "ghcver", "ghc844", 1).
'''.split('\n')))


@pytest.fixture(scope="module")
def example_hydra_jobsets(generated_hydra_builder_output):
    return generated_hydra_builder_output[0][None]

GS = [ "ghc822", "ghc844" ]
top_level = [
    "regular master heads",
    "regular master submodules",
    "regular feat1 heads",
    "regular dev heads",
    "pullreq bugfix9 heads",
    "pullreq bugfix9 submodules",
    "pullreq blah heads",
    "pullreq blah submodules",
]

def test_example_internal_count(generated_bldconfigs):
    print('### bldcfgs:')
    for each in generated_bldconfigs.cfg_build_configs:
        print(each.projectname, each.branchtype, each.branchname, each.strategy)
    assert len(GS) * len(top_level) == len(generated_bldconfigs.cfg_build_configs)

def test_example_internal_no_blah_regular_submods(generated_bldconfigs):
    for each in generated_bldconfigs.cfg_build_configs:
        assert not (each.branchtype == "regular" and
                    each.branchname == "blah" and
                    each.strategy == "submodules")

def test_example_internal_no_blah_regular_HEADs(generated_bldconfigs):
    for each in generated_bldconfigs.cfg_build_configs:
        assert not (each.branchtype == "regular" and
                    each.branchname == "blah" and
                    each.strategy == "HEADs")


def test_example_internal_bugfix9_pullreq_submods(generated_bldconfigs):
    for each in [ BldConfig(projectname="R10",
                            branchtype="pullreq",
                            branchname="bugfix9",
                            strategy="submodules",
                            description=PR_Grouped("bugfix9"),
                            blds=[BldRepoRev("R10", "master", "project_primary"),
                                  BldRepoRev("R3", "r3_master_head^9", "project_primary"),
                                  BldRepoRev("R4", "bugfix9", "8192"),
                            ],
                            bldvars=[BldVariable("R10", "ghcver", G)])
                  for G in GS]:
        assert each in generated_bldconfigs.cfg_build_configs

def test_example_internal_bugfix9_pullreq_HEADs(generated_bldconfigs):
    for each in [ BldConfig(projectname="R10",
                            branchtype="pullreq",
                            branchname="bugfix9",
                            strategy="HEADs",
                            description=PR_Grouped("bugfix9"),
                            blds=[BldRepoRev("R10", "master", "project_primary"),
                                  BldRepoRev("R3", "master", "project_primary"),
                                  BldRepoRev("R4", "bugfix9", "8192"),
                            ],
                            bldvars=[BldVariable("R10", "ghcver", G)])
                  for G in GS]:
        assert each in generated_bldconfigs.cfg_build_configs

def test_example_internal_no_bugfix9_regular_submods(generated_bldconfigs):
    for each in generated_bldconfigs.cfg_build_configs:
        assert not (each.branchtype == "regular" and
                    each.branchname == "bugfix9" and
                    each.strategy == "submodules")

def test_example_internal_no_bugfix9_regular_HEADs(generated_bldconfigs):
    for each in generated_bldconfigs.cfg_build_configs:
        assert not (each.branchtype == "regular" and
                    each.branchname == "bugfix9" and
                    each.strategy == "HEADs")

def test_example_internal_no_feat1_regular_submodules(generated_bldconfigs):
    # Because feat1 is not a branch in R10, and all other repos are
    # submodules, there is no submodule-based specification that can
    # reference the feat1 branch, so this configuration should be
    # suppressed.
    for each in generated_bldconfigs.cfg_build_configs:
        assert not (each.branchtype == "regular" and
                    each.branchname == "feat1" and
                    each.strategy == "submodules")


def test_example_internal_feat1_regular_HEADs(generated_bldconfigs):
    for each in [ BldConfig(projectname="R10",
                            branchtype="regular",
                            branchname="feat1",
                            strategy="HEADs",
                            description=BranchReq("R10", "feat1"),
                            blds=[BldRepoRev("R10", "master", "project_primary"),
                                  BldRepoRev("R3", "master", "project_primary"),
                                  BldRepoRev("R4", "feat1", "project_primary"),
                            ],
                            bldvars=[BldVariable("R10", "ghcver", G)])
                  for G in GS]:
        assert each in generated_bldconfigs.cfg_build_configs

def test_example_internal_master_regular_submodules(generated_bldconfigs):
    for each in [ BldConfig(projectname="R10",
                            branchtype="regular",
                            branchname="master",
                            strategy="submodules",
                            description=BranchReq("R10", "master"),
                            blds=[BldRepoRev("R10", "master", "project_primary"),
                                  BldRepoRev("R3", "r3_master_head^9", "project_primary"),
                                  BldRepoRev("R4", "r4_master_head^1", "project_primary"),
                            ],
                            bldvars=[BldVariable("R10", "ghcver", G)])
                  for G in GS]:
        assert each in generated_bldconfigs.cfg_build_configs

def test_example_internal_master_regular_HEADs(generated_bldconfigs):
    for each in [ BldConfig(projectname="R10",
                            branchtype="regular",
                            branchname="master",
                            strategy="HEADs",
                            description=BranchReq("R10", "master"),
                            blds=[BldRepoRev("R10", "master", "project_primary"),
                                  BldRepoRev("R3", "master", "project_primary"),
                                  BldRepoRev("R4", "master", "project_primary"),
                            ],
                            bldvars=[BldVariable("R10", "ghcver", G)])
                  for G in GS]:
        assert each in generated_bldconfigs.cfg_build_configs

def test_example_internal_dev_regular_submodules(generated_bldconfigs):
    # Because dev is not a branch in R10, and all other repos are
    # submodules, there is no submodule-based specification that can
    # reference the dev branch, so this configuration should be
    # suppressed.
    for each in generated_bldconfigs.cfg_build_configs:
        assert not (each.branchtype == "regular" and
                    each.branchname == "dev" and
                    each.strategy == "submodules")



def test_example_internal_dev_regular_HEADs(generated_bldconfigs):
    for each in [ BldConfig(projectname="R10",
                            branchtype="regular",
                            branchname="dev",
                            strategy="HEADs",
                            description=BranchReq("R10", "dev"),
                            blds=[BldRepoRev("R10", "master", "project_primary"),
                                  BldRepoRev("R3", "master", "project_primary"),
                                  BldRepoRev("R4", "master", "project_primary"),
                            ],
                            bldvars=[BldVariable("R10", "ghcver", G)])
                  for G in GS]:
        assert each in generated_bldconfigs.cfg_build_configs


def test_example_hydra_count(example_hydra_jobsets):
    print('##### OUTPUT:')
    print(example_hydra_jobsets)
    assert len(GS) * len(top_level) == len(json.loads(example_hydra_jobsets))

def test_example_hydra_master_submodules(example_hydra_jobsets):
    expected = dict([
        ( "master.submodules-%s" % (G), {
            "checkinterval": 600,
            "description": "Build configuration: brr34:R10, brr34:R3, brr34:R4, ghcver=%s" % (G),
            "emailoverride": "",
            "enabled": 1,
            "enableemail": False,
            "hidden": False,
            "inputs": {
                "R10-src": {
                    "emailresponsible": False,
                    "type": "git",
                    "value": "https://gitlab.com/r10_url master"
                },
                "R3-src": {
                    "emailresponsible": False,
                    "type": "git",
                    "value": "https://github.com/r3_url r3_master_head^9"
                },
                "R4-src": {
                    "emailresponsible": False,
                    "type": "git",
                    "value": "https://github.com/r4_url r4_master_head^1"
                },
                "ghcver": {
                    "emailresponsible": False,
                    "type": "string",
                    "value": G
                },
                "variant": {
                    "emailresponsible": False,
                    "type": "string",
                    "value": "|branch=master|strategy=submodules"
                },
            },
            "keepnr": 3,
            "nixexprinput": "R10-src",
            "nixexprpath": "./release.nix",
            "schedulingshares": 1
        }) for G in GS ])
    for each in expected:
        print(each)
        actual = json.loads(example_hydra_jobsets)
        assert each in actual
        assert expected[each] == actual[each]

def test_example_hydra_master_heads(example_hydra_jobsets):
    expected = dict([
          ("master.HEADs-%s" % (G), {
             "checkinterval": 600,
             "description": "Build configuration: brr32:R10, brr32:R3, brr32:R4, ghcver=%s" % (G),
             "emailoverride": "",
             "enabled": 1,
             "enableemail": False,
             "hidden": False,
             "inputs": {
                 "R10-src": {
                     "emailresponsible": False,
                     "type": "git",
                     "value": "https://gitlab.com/r10_url master"
                 },
                 "R3-src": {
                     "emailresponsible": False,
                     "type": "git",
                     "value": "https://github.com/r3_url master"
                 },
                 "R4-src": {
                     "emailresponsible": False,
                     "type": "git",
                     "value": "https://github.com/r4_url master"
                 },
                 "ghcver": {
                     "emailresponsible": False,
                     "type": "string",
                     "value": G
                 },
                 "variant": {
                     "emailresponsible": False,
                     "type": "string",
                     "value": "|branch=master|strategy=HEADs"
                 },
             },
             "keepnr": 3,
             "nixexprinput": "R10-src",
             "nixexprpath": "./release.nix",
             "schedulingshares": 1
         }) for G in GS ])
    for each in expected:
        print(each)
        actual = json.loads(example_hydra_jobsets)
        assert each in actual
        assert expected[each] == actual[each]

def test_example_hydra_feat1_heads(example_hydra_jobsets):
    expected = dict([
        ( "feat1.HEADs-%s" % (G), {
            "checkinterval": 600,
            "description": "Build configuration: brr32:R10, brr32:R3, brr32:R4, ghcver=%s" % (G),
            "emailoverride": "",
            "enabled": 1,
            "enableemail": False,
            "hidden": False,
            "inputs": {
                "R10-src": {
                    "emailresponsible": False,
                    "type": "git",
                    "value": "https://gitlab.com/r10_url master"
                },
                "R3-src": {
                    "emailresponsible": False,
                    "type": "git",
                    "value": "https://github.com/r3_url master"
                },
                "R4-src": {
                    "emailresponsible": False,
                    "type": "git",
                    "value": "https://github.com/r4_url feat1"
                },
                "ghcver": {
                    "emailresponsible": False,
                    "type": "string",
                    "value": G
                },
                "variant": {
                    "emailresponsible": False,
                    "type": "string",
                    "value": "|branch=feat1|strategy=HEADs"
                },
            },
            "keepnr": 3,
            "nixexprinput": "R10-src",
            "nixexprpath": "./release.nix",
            "schedulingshares": 1
        }) for G in GS ])
    for each in expected:
        print(each)
        actual = json.loads(example_hydra_jobsets)
        assert each in actual
        assert expected[each] == actual[each]

def test_example_hydra_dev_heads(example_hydra_jobsets):
    expected = dict([
        ( "dev.HEADs-%s" % (G), {
            "checkinterval": 600,
            "description": "Build configuration: brr32:R10, brr32:R3, brr32:R4, ghcver=%s" % (G),
            "emailoverride": "",
            "enabled": 1,
            "enableemail": False,
            "hidden": False,
            "inputs": {
                "R10-src": {
                    "emailresponsible": False,
                    "type": "git",
                    "value": "https://gitlab.com/r10_url master"
                },
                "R3-src": {
                    "emailresponsible": False,
                    "type": "git",
                    "value": "https://github.com/r3_url master"
                },
                "R4-src": {
                    "emailresponsible": False,
                    "type": "git",
                    "value": "https://github.com/r4_url master"
                },
                "ghcver": {
                    "emailresponsible": False,
                    "type": "string",
                    "value": G
                },
                "variant": {
                    "emailresponsible": False,
                    "type": "string",
                    "value": "|branch=dev|strategy=HEADs"
                },
            },
            "keepnr": 3,
            "nixexprinput": "R10-src",
            "nixexprpath": "./release.nix",
            "schedulingshares": 1
        }) for G in GS  ])
    for each in expected:
        print(each)
        actual = json.loads(example_hydra_jobsets)
        assert each in actual
        assert expected[each] == actual[each]

def test_example_hydra_master_bugfix9_submodules(example_hydra_jobsets):
    expected = dict([
        ( "PR-bugfix9.submodules-%s" % (G), {
            "checkinterval": 600,
            "description": "Build configuration: brr34:R10, brr34:R3, PR8192-brr31:R4, ghcver=%s" % (G),
            "emailoverride": "",
            "enabled": 1,
            "enableemail": False,
            "hidden": False,
            "inputs": {
                "R10-src": {
                    "emailresponsible": False,
                    "type": "git",
                    "value": "https://gitlab.com/r10_url master"
                },
                "R3-src": {
                    "emailresponsible": False,
                    "type": "git",
                    "value": "https://github.com/r3_url r3_master_head^9"
                },
                "R4-src": {
                    "emailresponsible": False,
                    "type": "git",
                    "value": "https://github.com/remote_R4_y bugfix9"
                },
                "ghcver": {
                    "emailresponsible": False,
                    "type": "string",
                    "value": G
                },
                 "variant": {
                     "emailresponsible": False,
                     "type": "string",
                     "value": "|branch=bugfix9|strategy=submodules|PR"
                 },
            },
            "keepnr": 3,
            "nixexprinput": "R10-src",
            "nixexprpath": "./release.nix",
            "schedulingshares": 1
        }) for G in GS  ])
    for each in expected:
        print(each)
        actual = json.loads(example_hydra_jobsets)
        assert each in actual
        assert expected[each] == actual[each]

def test_example_hydra_master_bugfix9_heads(example_hydra_jobsets):
    expected = dict([
        ( "PR-bugfix9.HEADs-%s" % (G), {
            "checkinterval": 600,
            "description": "Build configuration: brr32:R10, brr32:R3, PR8192-brr31:R4, ghcver=%s" % (G),
             "emailoverride": "",
             "enabled": 1,
             "enableemail": False,
             "hidden": False,
             "inputs": {
                 "R10-src": {
                     "emailresponsible": False,
                     "type": "git",
                     "value": "https://gitlab.com/r10_url master"
                 },
                 "R3-src": {
                     "emailresponsible": False,
                     "type": "git",
                     "value": "https://github.com/r3_url master"
                 },
                 "R4-src": {
                     "emailresponsible": False,
                     "type": "git",
                     "value": "https://github.com/remote_R4_y bugfix9"
                 },
                 "ghcver": {
                     "emailresponsible": False,
                     "type": "string",
                     "value": G
                 },
                 "variant": {
                     "emailresponsible": False,
                     "type": "string",
                     "value": "|branch=bugfix9|strategy=HEADs|PR"
                 },
             },
             "keepnr": 3,
             "nixexprinput": "R10-src",
             "nixexprpath": "./release.nix",
             "schedulingshares": 1
         }) for G in GS  ])
    for each in expected:
        print(each)
        actual = json.loads(example_hydra_jobsets)
        assert each in actual
        assert expected[each] == actual[each]

build_results = [
    { "name": n % v,
      "nrtotal" : 123,
      "nrsucceeded": 0 if 'ghc822' == v else 123,
      "nrfailed": 123 if 'ghc822' == v else 0,
      "nrscheduled": 0,
      "haserrormsg": False,
    }
    for n in [
            "master.HEADs-%s",
            "master.submodules-%s",
            "feat1.HEADs-%s",
            "dev.HEADs-%s",
            "PR-bugfix9.HEADs-%s",
            "PR-bugfix9.submodules-%s",
            "PR-blah.HEADs-%s",
            "PR-blah.submodules-%s",
    ]
    for v in [ "ghc822", "ghc844" ]
]

prior = [
]
