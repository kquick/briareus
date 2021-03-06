import Briareus.Input.Parser as Parser
import Briareus.Input.Description as D
from test_example import expected_repo_info


def test_input_parser():
    parser = Parser.BISParser()
    inp = parser.parse(input_spec)
    assert expected_inp == inp

input_spec = open('test/inp_example').read()

def test_example_facts(generated_facts):
    assert expected_facts == list(map(str, generated_facts))


expected_inp = D.InputDesc(
    PNAME="Project #1",
    RL = sorted([ D.RepoDesc(repo_name="R1", repo_url="https://github.com/r1_url", project_repo=True),
                  D.RepoDesc(repo_name="R2", repo_url="https://github.com/r2_url"),
                  D.RepoDesc(repo_name="R3", repo_url="https://github.com/r3_url"),
                  D.RepoDesc(repo_name="R5", repo_url="https://github.com/r5_url"),
                  D.RepoDesc(repo_name="R6", repo_url="https://github.com/r6_url"),
    ]),
    BL = sorted([ D.BranchDesc(branch_name="master"),
                  D.BranchDesc(branch_name="feat1"),
                  D.BranchDesc(branch_name="dev"),
    ]),
    VAR = [ D.VariableDesc(variable_name="ghcver",
                           variable_values=["ghc844", "ghc865", "ghc881"]),
            D.VariableDesc(variable_name="c_compiler",
                           variable_values=["gnucc", "clang"]),
    ],
    REP = {'logic': """
project_owner("Project #1", "george@_company.com").

project_owner("R3", "john@not_a_company.com").

enable(email, "fred@nocompany.com", notify(_, "Project #1", _)).
enable(email, "eddy@nocompany.com", notify(_, "Project #1", _)).
enable(email, "sam@not_a_company.com", notify(_, "Project #1", _)).
enable(email, "john@_company.com", notify(_, "Project #1", _)).
enable(email, "anne@nocompany.com", notify(master_submodules_broken, "Project #1", _)).
enable(email, "betty@nocompany.com", notify(variable_failing, "Project #1", _)).

enable(forge_status, "Project #1", _).
      """
    }
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
project("Project #1").
project("Project #1", "R1").
repo("Project #1", "R1").
default_main_branch("master").
repo("Project #1", "R2").
repo("Project #1", "R3").
repo("Project #1", "R5").
repo("Project #1", "R6").
subrepo("R1", "R2").
subrepo("R1", "R3").
subrepo("R1", "R4").
subrepo("R1", "R7").
branchreq("Project #1", "master").
branchreq("Project #1", "feat1").
branchreq("Project #1", "dev").
branch("R1", "master").
branch("R1", "feat1").
branch("R2", "bugfix9").
branch("R2", "master").
branch("R3", "master").
branch("R5", "master").
branch("R5", "dev").
branch("R6", "master").
branch("R6", "feat1").
branch("R3", "blah").
branch("R5", "blah").
branch("R4", "master").
branch("R4", "feat1").
branch("R7", "master").
branch("R5", "bugfix9").
branch_ref("R1", "master", "R1-master-ref").
branch_ref("R1", "feat1", "r1-feat1-ref").
branch_ref("R2", "bugfix9", "r2-bugfix9-ref").
branch_ref("R2", "master", "R2-master-ref").
branch_ref("R3", "master", "R3-master-ref").
branch_ref("R5", "master", "R5-master-ref").
branch_ref("R5", "dev", "r5-dev-ref").
branch_ref("R6", "master", "R6-master-ref").
branch_ref("R6", "feat1", "r6-feat1-ref").
branch_ref("R3", "blah", "r3-blah-ref").
branch_ref("R5", "blah", "r5-blah-ref").
branch_ref("R4", "master", "R4-master-ref").
branch_ref("R4", "feat1", "r4-feat1-ref").
branch_ref("R7", "master", "R7-master-ref").
branch_ref("R5", "bugfix9", "r5-bugfix9-ref").
pullreq("R1", "1", "blah", "r1_blah_mergeref", prsts_active, "nick", "nick@bad.seeds").
pullreq("R4", "8192", "bugfix9", "r4_bf9_mergeref", prsts_active, "ozzie", "ozzie@crazy.train").
pullreq("R2", "23", "bugfix9", "r2_b9_mergeref", prsts_active, "banana", "").
pullreq("R3", "11", "blah", "r3_blah_mergeref", prsts_active, "nick", "nick@bad.seeds").
pullreq("R3", "22", "closed_pr", "r3_CLOSED_mergeref", prsts_closed, "done", "done@already.yo").
pullreq("R3", "33", "merged_pr", "r3_MERGED_mergeref", prsts_merged, "done", "done@already.yo").
pullreq("R6", "111", "blah", "r6_blah_mergeref", prsts_active, "nick", "nick@bad.seeds").
pullreq("R2", "1111", "blah", "r2_blah_mergeref", prsts_active, "not_nick", "not_nick@bad.seeds").
submodule("R1", project_primary, "master", "R2", "r2_master_head").
submodule("R1", project_primary, "master", "R3", "r3_master_head^3").
submodule("R1", project_primary, "master", "R4", "r4_master_head^1").
submodule("R1", project_primary, "feat1", "R2", "r2_master_head^1").
submodule("R1", project_primary, "feat1", "R3", "r3_master_head").
submodule("R1", project_primary, "feat1", "R4", "r4_feat1_head^2").
submodule("R1", "1", "blah", "R2", "r2_master_head^22").
submodule("R1", "1", "blah", "R3", "r3_master_head").
submodule("R1", "1", "blah", "R7", "r7_master_head^4").
varname("Project #1", "ghcver").
varname("Project #1", "c_compiler").
varvalue("Project #1", "ghcver", "ghc844", 0).
varvalue("Project #1", "ghcver", "ghc865", 1).
varvalue("Project #1", "ghcver", "ghc881", 2).
varvalue("Project #1", "c_compiler", "gnucc", 0).
varvalue("Project #1", "c_compiler", "clang", 1).
'''.split('\n')))

# Note: the above does not contain branch("R2", "bugfix9").  This is
# because the optimization in InternalOps previously determined that
# bugfix9 was a pullreq on R2, so it suppressed the query.
