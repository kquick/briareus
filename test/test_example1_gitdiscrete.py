from Briareus.Input.Operations import input_desc_and_VCS_info
import Briareus.VCS.GitForge
from test_example import expected_repo_info
import json
import pytest
from unittest.mock import patch
from FakeForge import (fake_forge, get_github_api_url_local,
                       get_gitlab_api_url_local,
                       github_gitmodules_contents,
                       github_submodule_contents,
                       github_branch,
                       gitlab_branch,
                       github_pullreq,
                       github_user)


input_spec = open('test/inp_example').read()

fakeforge_port = 4322


@patch.object(Briareus.VCS.GitForge.GitHubInfo, 'get_api_url')
def test_gitinfo(get_hub_api_url, actor_system, fake_forge):
    """Tests to ensure that the GetGitInfo discrete REST queries actor
       returned information is translated into the proper repo
       information for Briareus to use.
    """
    get_hub_api_url.side_effect = get_github_api_url_local(fakeforge_port)

    input_desc, repo_info = input_desc_and_VCS_info(input_spec, actor_system=actor_system)
    assert repo_info == expected_repo_info


# The blah is a pullreq in R1, with pullreqs in R2, R3, and R6:
#
#   * R2 is a submodule and does not have the branch, so the
#     submodules build should honor the submodule ref, but the HEADs
#     build should build from the R2 PR.
#
#   * R3 is similar to R2 except that there is also a blah branch in
#     the R3 primary repo.  This branch will be ignored because the
#     submodule takes precedence.
#
#   * R6 is not a submodule but a top level repo, so the submodules
#     build should build from the R6 PR as well as the HEADs build.


r1_gitmodules_master = b'''[submodule "r2_submod"]
	path = sub/r2
	url = https://github.com/r2_url
[submodule "r3-submod"]
	path = sub/r3
	url = https://github.com/r3_url
[submodule "r4-sub"]
	path = deps/r4
	url = https://github.com/r4_url
'''


r1_gitmodules_blah = b'''[submodule "r2_submod"]
	path = sub/r2
	url = https://github.com/r2_url
[submodule "r3-submod"]
	path = sub/r3
	url = https://github.com/r3_url
[submodule "r7-sub"]
	path = deps/r7
	url = https://github.com/r7_url
'''


r1_gitmodules_feat1 = r1_gitmodules_master


r2_gitmodules_master = b'''[submodule "r3_sub"]
	path = sub/r3
	url = https://github.com/r3_url
[submodule "r5-submod"]
	path = sub/r5
	url = https://github.com/r5_url
[submodule "r4-sub"]
	path = deps/r4
	url = https://github.com/r4_url
'''


r10_gitmodules_master = b'''[submodule "r3-submod"]
	path = sub/r3
	url = https://github.com/r3_url
[submodule "r4-sub"]
	path = deps/r4
	url = https://github.com/r4_url
'''


r10_gitmodules_devtest = r10_gitmodules_master


forge_responses = {

    ## R1 branches

    '/repos/r1_url/branches':
    json.dumps([
        github_branch('r1', 'https://github.com/r1_url', 'feat1'),
        github_branch('R1', 'https://github.com/r1_url', 'master'),
    ]).encode('utf-8'),

    '/repos/r2_url/branches':
    json.dumps([
        github_branch('r2', 'https://github.com/r2_url', 'bugfix9'),
        github_branch('R2', 'https://github.com/r2_url', 'master'),
    ]).encode('utf-8'),

    '/repos/r3_url/branches':
    json.dumps([
        github_branch('r3', 'https://github.com/r3_url', 'blah'),
        github_branch('R3', 'https://github.com/r3_url', 'master'),
    ]).encode('utf-8'),

    '/repos/r4_url/branches':
    json.dumps([
        github_branch('r4', 'https://github.com/r4_url', 'feat1'),
        github_branch('R4', 'https://github.com/r4_url', 'master'),
    ]).encode('utf-8'),


    '/repos/r5_url/branches':
    json.dumps([
        github_branch('r5', 'https://github.com/r5_url', 'blah'),
        github_branch('r5', 'https://github.com/r5_url', 'dev'),
        github_branch('r5', 'https://github.com/r5_url', 'bugfix9'),
        github_branch('R5', 'https://github.com/r5_url', 'master'),
    ]).encode('utf-8'),

    '/repos/r6_url/branches':
    json.dumps([
        github_branch('r6', 'https://github.com/r6_url', 'feat1'),
        github_branch('R6', 'https://github.com/r6_url', 'master'),
    ]).encode('utf-8'),

    '/repos/r7_url/branches': b'''
[
  {
    "name": "master",
    "commit": {
      "sha": "R7-master-ref",
      "url": "https://github.com/r7_url/commits/R7-master-ref"
    },
    "protected": false
  }
]
    ''',

    '/api/v4/projects/r10_url/repository/branches':
    json.dumps([
        gitlab_branch("R10", "https://gitlab.com/r10_url", "master"),
    ]).encode('utf-8'),



    # ############################################################

    '/repos/r1_url/pulls?state=all': b'''
[
  {
    "url": "https://github.com/r1_url/pulls/1",
    "id": 365427239,
    "node_id": "MDExOlB1bGxSZXF1ZXN0MzY1NDI3MjM5",
    "html_url": "https://localhost/r1_url/pull/1",
    "diff_url": "https://localhost/r1_url/pull/1.diff",
    "patch_url": "https://localhost/r1_url/pull/1.patch",
    "issue_url": "https://github.com/r1_url/issues/1",
    "number": 1,
    "state": "open",
    "locked": false,
    "title": "pr#19",
    "user": {
      "login": "nick",
      "id": 555,
      "type": "User",
      "site_admin": false
    },
    "body": "",
    "created_at": "2020-01-21T17:35:14Z",
    "updated_at": "2020-01-26T19:35:44Z",
    "closed_at": null,
    "merged_at": null,
    "merge_commit_sha": "ra_blah_merge_commit_ref",
    "assignee": null,
    "assignees": [

    ],
    "requested_reviewers": [

    ],
    "requested_teams": [

    ],
    "labels": [

    ],
    "milestone": null,
    "draft": false,
    "commits_url": "https://github.com/r1_url/pulls/1/commits",
    "review_comments_url": "https://github.com/r1_url/pulls/1/comments",
    "review_comment_url": "https://github.com/r1_url/pulls/comments{/number}",
    "comments_url": "https://github.com/r1_url/issues/1/comments",
    "statuses_url": "https://github.com/r1_url/statuses/toad_mergeref",
    "head": {
      "label": "r1_repo:blah",
      "ref": "blah",
      "sha": "r1_blah_mergeref",
      "user": {
        "login": "nick",
        "id": 555,
        "type": "User",
        "site_admin": false
      },
      "repo": {
        "id": 235401723,
        "name": "r1_repo",
        "full_name": "proj_repo/r1_repo",
        "private": false,
        "owner": {
          "login": "alfred",
          "id": 55,
          "type": "User",
          "site_admin": false
        },
        "html_url": "https://github.com/remote_R1_b",
        "description": "r1 repo",
        "fork": false,
        "created_at": "2020-01-21T17:32:49Z",
        "updated_at": "2020-01-21T17:37:42Z",
        "pushed_at": "2020-01-26T19:35:45Z",
        "homepage": null,
        "size": 3,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": null,
        "has_issues": false,
        "has_projects": true,
        "has_downloads": true,
        "has_wiki": true,
        "has_pages": false,
        "forks_count": 0,
        "mirror_url": null,
        "archived": false,
        "disabled": false,
        "open_issues_count": 1,
        "license": null,
        "forks": 0,
        "open_issues": 1,
        "watchers": 0,
        "default_branch": "master"
      }
    },
    "base": {
      "label": "r1_repo:master",
      "ref": "master",
      "sha": "r1_master_ref",
      "user": {
        "login": "alfred",
        "id": 55,
        "type": "User",
        "site_admin": false
      },
      "repo": {
        "id": 235401723,
        "name": "r1_repo",
        "full_name": "proj_name/r1_repo",
        "private": false,
        "owner": {
          "login": "alfred",
          "id": 55,
          "type": "User",
          "site_admin": false
        },
        "html_url": "https://localhost/r1_url",
        "description": "r1 repo",
        "fork": false,
        "url": "https://github.com/r1_url",
        "created_at": "2020-01-21T17:32:49Z",
        "updated_at": "2020-01-21T17:37:42Z",
        "pushed_at": "2020-01-26T19:35:45Z",
        "homepage": null,
        "size": 3,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": null,
        "has_issues": false,
        "has_projects": true,
        "has_downloads": true,
        "has_wiki": true,
        "has_pages": false,
        "forks_count": 0,
        "mirror_url": null,
        "archived": false,
        "disabled": false,
        "open_issues_count": 1,
        "license": null,
        "forks": 0,
        "open_issues": 1,
        "watchers": 0,
        "default_branch": "master"
      }
    },
    "_links": {
      "self": {
        "href": "https://github.com/r1_url/pulls/1"
      },
      "html": {
        "href": "https://localhost/r1_url/pull/1"
      },
      "issue": {
        "href": "https://github.com/r1_url/issues/1"
      },
      "comments": {
        "href": "https://github.com/r1_url/issues/1/comments"
      },
      "review_comments": {
        "href": "https://github.com/r1_url/pulls/1/comments"
      },
      "review_comment": {
        "href": "https://github.com/r1_url/pulls/comments{/number}"
      },
      "commits": {
        "href": "https://github.com/r1_url/pulls/1/commits"
      },
      "statuses": {
        "href": "https://github.com/r1_url/statuses/blah_mergeref"
      }
    },
    "author_association": "OWNER",
    "active_lock_reason": null
  }
]
    ''',

    ## R2 pulls

    '/repos/r2_url/pulls?state=all': json.dumps([
        github_pullreq('https://github.com/r2_url', '23', 'bugfix9',
                       'r2_b9_mergeref', 'add fantasticness',
                       'https://github.com/remote_r2_a',
                       'banana', 553),
        github_pullreq('https://github.com/r2_url', '1111', 'blah',
                       'r2_blah_mergeref', 'blah also',
                       'https://github.com/remote_r2_pr1111_url',
                       'not_nick', 554),
    ]).encode('utf-8'),


    ## R3 pulls

    '/repos/r3_url/pulls?state=all': b'''
[
  {
    "url": "https://github.com/r3_url/pulls/22",
    "id": 365427226,
    "node_id": "MDExOlB1bGxSZXF1ZXN0MzY1NDI3MjM5",
    "html_url": "https://localhost/r3_url/pull/22",
    "diff_url": "https://localhost/r3_url/pull/22.diff",
    "patch_url": "https://localhost/r3_url/pull/22.patch",
    "issue_url": "https://github.com/r3_url/issues/22",
    "number": 22,
    "state": "closed",
    "locked": false,
    "title": "ignored because closed",
    "user": {
      "login": "done",
      "id": 552,
      "type": "User",
      "site_admin": false
    },
    "body": "",
    "created_at": "2020-01-21T17:35:14Z",
    "updated_at": "2020-01-26T22:35:44Z",
    "closed_at": null,
    "merged_at": null,
    "merge_commit_sha": "r3_closed_pr_merge_commit_ref",
    "assignee": null,
    "assignees": [

    ],
    "requested_reviewers": [

    ],
    "requested_teams": [

    ],
    "labels": [

    ],
    "milestone": null,
    "draft": false,
    "commits_url": "https://github.com/r3_url/pulls/22/commits",
    "review_comments_url": "https://github.com/r3_url/pulls/22/comments",
    "review_comment_url": "https://github.com/r3_url/pulls/comments{/number}",
    "comments_url": "https://github.com/r3_url/issues/22/comments",
    "statuses_url": "https://github.com/r3_url/statuses/closed_pr_mergeref",
    "head": {
      "label": "r3_repo:closed_pr",
      "ref": "closed_pr",
      "sha": "r3_CLOSED_mergeref",
      "user": {
        "login": "done",
        "id": 552,
        "type": "User",
        "site_admin": false
      },
      "repo": {
        "id": 225401722,
        "name": "r3_repo",
        "full_name": "proj_repo/r3_repo",
        "private": false,
        "owner": {
          "login": "higgins",
          "id": 52,
          "type": "User",
          "site_admin": false
        },
        "html_url": "https://github.com/remote_r3_CLOSED_url",
        "description": "r3 repo",
        "fork": false,
        "created_at": "2020-01-21T17:32:49Z",
        "updated_at": "2020-01-21T17:37:42Z",
        "pushed_at": "2020-01-26T22:35:45Z",
        "homepage": null,
        "size": 3,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": null,
        "has_issues": false,
        "has_projects": true,
        "has_downloads": true,
        "has_wiki": true,
        "has_pages": false,
        "forks_count": 0,
        "mirror_url": null,
        "archived": false,
        "disabled": false,
        "open_issues_count": 1,
        "license": null,
        "forks": 0,
        "open_issues": 1,
        "watchers": 0,
        "default_branch": "master"
      }
    },
    "base": {
      "label": "r3_repo:master",
      "ref": "master",
      "sha": "r3_master_ref",
      "user": {
        "login": "higgins",
        "id": 52,
        "type": "User",
        "site_admin": false
      },
      "repo": {
        "id": 225401722,
        "name": "r3_repo",
        "full_name": "proj_name/r3_repo",
        "private": false,
        "owner": {
          "login": "higgins",
          "id": 52,
          "type": "User",
          "site_admin": false
        },
        "html_url": "https://localhost/r3_url",
        "description": "r3 repo",
        "fork": false,
        "url": "https://github.com/r3_url",
        "created_at": "2020-01-21T17:32:49Z",
        "updated_at": "2020-01-21T17:37:42Z",
        "pushed_at": "2020-01-26T22:35:45Z",
        "homepage": null,
        "size": 3,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": null,
        "has_issues": false,
        "has_projects": true,
        "has_downloads": true,
        "has_wiki": true,
        "has_pages": false,
        "forks_count": 0,
        "mirror_url": null,
        "archived": false,
        "disabled": false,
        "open_issues_count": 1,
        "license": null,
        "forks": 0,
        "open_issues": 1,
        "watchers": 0,
        "default_branch": "master"
      }
    },
    "_links": {
      "self": {
        "href": "https://github.com/r3_url/pulls/22"
      },
      "html": {
        "href": "https://localhost/r3_url/pull/22"
      },
      "issue": {
        "href": "https://github.com/r3_url/issues/22"
      },
      "comments": {
        "href": "https://github.com/r3_url/issues/22/comments"
      },
      "review_comments": {
        "href": "https://github.com/r3_url/pulls/22/comments"
      },
      "review_comment": {
        "href": "https://github.com/r3_url/pulls/comments{/number}"
      },
      "commits": {
        "href": "https://github.com/r3_url/pulls/22/commits"
      },
      "statuses": {
        "href": "https://github.com/r3_url/statuses/closed_pr_mergeref"
      }
    },
    "author_association": "OWNER",
    "active_lock_reason": null
  },


  {
    "url": "https://github.com/r3_url/pulls/11",
    "id": 365427119,
    "node_id": "MDExOlB1bGxSZXF1ZXN0MzY1NDI3MjM5",
    "html_url": "https://localhost/r3_url/pull/11",
    "diff_url": "https://localhost/r3_url/pull/11.diff",
    "patch_url": "https://localhost/r3_url/pull/11.patch",
    "issue_url": "https://github.com/r3_url/issues/11",
    "number": 11,
    "state": "open",
    "locked": false,
    "title": "blah started",
    "user": {
      "login": "nick",
      "id": 555,
      "type": "User",
      "site_admin": false
    },
    "body": "",
    "created_at": "2020-01-21T17:35:14Z",
    "updated_at": "2020-01-26T11:35:44Z",
    "closed_at": null,
    "merged_at": null,
    "merge_commit_sha": "r3_blah_merge_commit_ref",
    "assignee": null,
    "assignees": [

    ],
    "requested_reviewers": [

    ],
    "requested_teams": [

    ],
    "labels": [

    ],
    "milestone": null,
    "draft": false,
    "commits_url": "https://github.com/r3_url/pulls/11/commits",
    "review_comments_url": "https://github.com/r3_url/pulls/11/comments",
    "review_comment_url": "https://github.com/r3_url/pulls/comments{/number}",
    "comments_url": "https://github.com/r3_url/issues/11/comments",
    "statuses_url": "https://github.com/r3_url/statuses/blah_mergeref",
    "head": {
      "label": "r3_repo:blah",
      "ref": "blah",
      "sha": "r3_blah_mergeref",
      "user": {
        "login": "nick",
        "id": 555,
        "type": "User",
        "site_admin": false
      },
      "repo": {
        "id": 115401711,
        "name": "r3_repo",
        "full_name": "proj_repo/r3_repo",
        "private": false,
        "owner": {
          "login": "higgins",
          "id": 52,
          "type": "User",
          "site_admin": false
        },
        "html_url": "https://github.com/remote_r3_pr11_url",
        "description": "r3 repo",
        "fork": false,
        "created_at": "2020-01-21T17:32:49Z",
        "updated_at": "2020-01-21T17:37:42Z",
        "pushed_at": "2020-01-26T22:35:45Z",
        "homepage": null,
        "size": 3,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": null,
        "has_issues": false,
        "has_projects": true,
        "has_downloads": true,
        "has_wiki": true,
        "has_pages": false,
        "forks_count": 0,
        "mirror_url": null,
        "archived": false,
        "disabled": false,
        "open_issues_count": 1,
        "license": null,
        "forks": 0,
        "open_issues": 1,
        "watchers": 0,
        "default_branch": "master"
      }
    },
    "base": {
      "label": "r3_repo:master",
      "ref": "master",
      "sha": "r3_master_ref",
      "user": {
        "login": "higgins",
        "id": 52,
        "type": "User",
        "site_admin": false
      },
      "repo": {
        "id": 115401711,
        "name": "r3_repo",
        "full_name": "proj_name/r3_repo",
        "private": false,
        "owner": {
          "login": "higgins",
          "id": 52,
          "type": "User",
          "site_admin": false
        },
        "html_url": "https://localhost/r3_url",
        "description": "r3 repo",
        "fork": false,
        "url": "https://github.com/r3_url",
        "created_at": "2020-01-21T17:32:49Z",
        "updated_at": "2020-01-21T17:37:42Z",
        "pushed_at": "2020-01-26T22:35:45Z",
        "homepage": null,
        "size": 3,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": null,
        "has_issues": false,
        "has_projects": true,
        "has_downloads": true,
        "has_wiki": true,
        "has_pages": false,
        "forks_count": 0,
        "mirror_url": null,
        "archived": false,
        "disabled": false,
        "open_issues_count": 1,
        "license": null,
        "forks": 0,
        "open_issues": 1,
        "watchers": 0,
        "default_branch": "master"
      }
    },
    "_links": {
      "self": {
        "href": "https://github.com/r3_url/pulls/11"
      },
      "html": {
        "href": "https://localhost/r3_url/pull/11"
      },
      "issue": {
        "href": "https://github.com/r3_url/issues/11"
      },
      "comments": {
        "href": "https://github.com/r3_url/issues/11/comments"
      },
      "review_comments": {
        "href": "https://github.com/r3_url/pulls/11/comments"
      },
      "review_comment": {
        "href": "https://github.com/r3_url/pulls/comments{/number}"
      },
      "commits": {
        "href": "https://github.com/r3_url/pulls/11/commits"
      },
      "statuses": {
        "href": "https://github.com/r3_url/statuses/blah_mergeref"
      }
    },
    "author_association": "OWNER",
    "active_lock_reason": null
  },



  {
    "url": "https://github.com/r3_url/pulls/33",
    "id": 365427336,
    "node_id": "MDExOlB1bGxSZXF1ZXN0MzY1NDI3MjM5",
    "html_url": "https://localhost/r3_url/pull/33",
    "diff_url": "https://localhost/r3_url/pull/33.diff",
    "patch_url": "https://localhost/r3_url/pull/33.patch",
    "issue_url": "https://github.com/r3_url/issues/33",
    "number": 33,
    "state": "merged",
    "locked": false,
    "title": "ignored because merged",
    "user": {
      "login": "done",
      "id": 552,
      "type": "User",
      "site_admin": false
    },
    "body": "",
    "created_at": "2020-01-21T17:35:14Z",
    "updated_at": "2020-01-26T33:35:44Z",
    "closed_at": null,
    "merged_at": "2020-01-26T33:35:44Z",
    "merge_commit_sha": "r3_merged_pr_merge_commit_ref",
    "assignee": null,
    "assignees": [

    ],
    "requested_reviewers": [

    ],
    "requested_teams": [

    ],
    "labels": [

    ],
    "milestone": null,
    "draft": false,
    "commits_url": "https://github.com/r3_url/pulls/33/commits",
    "review_comments_url": "https://github.com/r3_url/pulls/33/comments",
    "review_comment_url": "https://github.com/r3_url/pulls/comments{/number}",
    "comments_url": "https://github.com/r3_url/issues/33/comments",
    "statuses_url": "https://github.com/r3_url/statuses/merged_pr_mergeref",
    "head": {
      "label": "r3_repo:merged_pr",
      "ref": "merged_pr",
      "sha": "r3_MERGED_mergeref",
      "user": {
        "login": "done",
        "id": 552,
        "type": "User",
        "site_admin": false
      },
      "repo": {
        "id": 335401733,
        "name": "r3_repo",
        "full_name": "proj_repo/r3_repo",
        "private": false,
        "owner": {
          "login": "higgins",
          "id": 52,
          "type": "User",
          "site_admin": false
        },
        "html_url": "https://github.com/remote_r3_MERGED_url",
        "description": "r3 repo",
        "fork": false,
        "created_at": "2020-01-21T17:32:49Z",
        "updated_at": "2020-01-21T17:37:42Z",
        "pushed_at": "2020-01-26T33:35:45Z",
        "homepage": null,
        "size": 3,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": null,
        "has_issues": false,
        "has_projects": true,
        "has_downloads": true,
        "has_wiki": true,
        "has_pages": false,
        "forks_count": 0,
        "mirror_url": null,
        "archived": false,
        "disabled": false,
        "open_issues_count": 1,
        "license": null,
        "forks": 0,
        "open_issues": 1,
        "watchers": 0,
        "default_branch": "master"
      }
    },
    "base": {
      "label": "r3_repo:master",
      "ref": "master",
      "sha": "r3_master_ref",
      "user": {
        "login": "higgins",
        "id": 52,
        "type": "User",
        "site_admin": false
      },
      "repo": {
        "id": 335401733,
        "name": "r3_repo",
        "full_name": "proj_name/r3_repo",
        "private": false,
        "owner": {
          "login": "higgins",
          "id": 52,
          "type": "User",
          "site_admin": false
        },
        "html_url": "https://localhost/r3_url",
        "description": "r3 repo",
        "fork": false,
        "url": "https://github.com/r3_url",
        "created_at": "2020-01-21T17:32:49Z",
        "updated_at": "2020-01-21T17:37:42Z",
        "pushed_at": "2020-01-26T33:35:45Z",
        "homepage": null,
        "size": 3,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": null,
        "has_issues": false,
        "has_projects": true,
        "has_downloads": true,
        "has_wiki": true,
        "has_pages": false,
        "forks_count": 0,
        "mirror_url": null,
        "archived": false,
        "disabled": false,
        "open_issues_count": 1,
        "license": null,
        "forks": 0,
        "open_issues": 1,
        "watchers": 0,
        "default_branch": "master"
      }
    },
    "_links": {
      "self": {
        "href": "https://github.com/r3_url/pulls/33"
      },
      "html": {
        "href": "https://localhost/r3_url/pull/33"
      },
      "issue": {
        "href": "https://github.com/r3_url/issues/33"
      },
      "comments": {
        "href": "https://github.com/r3_url/issues/33/comments"
      },
      "review_comments": {
        "href": "https://github.com/r3_url/pulls/33/comments"
      },
      "review_comment": {
        "href": "https://github.com/r3_url/pulls/comments{/number}"
      },
      "commits": {
        "href": "https://github.com/r3_url/pulls/33/commits"
      },
      "statuses": {
        "href": "https://github.com/r3_url/statuses/merged_pr_mergeref"
      }
    },
    "author_association": "OWNER",
    "active_lock_reason": null
  }
]
    ''',


        '/repos/r4_url/pulls?state=all': b'''
[
  {
    "url": "https://github.com/r4_url/pulls/8192",
    "id": 36542781929,
    "node_id": "MDExOlB1bGxSZXF1ZXN0MzY1NDI3MjM5",
    "html_url": "https://localhost/r4_url/pull/8192",
    "diff_url": "https://localhost/r4_url/pull/8192.diff",
    "patch_url": "https://localhost/r4_url/pull/8192.patch",
    "issue_url": "https://github.com/r4_url/issues/8192",
    "number": 8192,
    "state": "open",
    "locked": false,
    "title": "fix ninth bug!",
    "user": {
      "login": "ozzie",
      "id": 559,
      "type": "User",
      "site_admin": false
    },
    "body": "",
    "created_at": "2020-01-21T17:35:14Z",
    "updated_at": "2020-01-26T11:35:44Z",
    "closed_at": null,
    "merged_at": null,
    "merge_commit_sha": "r4_bugfix9_merge_commit_ref",
    "assignee": null,
    "assignees": [

    ],
    "requested_reviewers": [

    ],
    "requested_teams": [

    ],
    "labels": [

    ],
    "milestone": null,
    "draft": false,
    "commits_url": "https://github.com/r4_url/pulls/8192/commits",
    "review_comments_url": "https://github.com/r4_url/pulls/8192/comments",
    "review_comment_url": "https://github.com/r4_url/pulls/comments{/number}",
    "comments_url": "https://github.com/r4_url/issues/8192/comments",
    "statuses_url": "https://github.com/r4_url/statuses/bugfix9_mergeref",
    "head": {
      "label": "r4_repo:bugfix9",
      "ref": "bugfix9",
      "sha": "r4_bf9_mergeref",
      "user": {
        "login": "ozzie",
        "id": 559,
        "type": "User",
        "site_admin": false
      },
      "repo": {
        "id": 115401711,
        "name": "r4_repo",
        "full_name": "proj_repo/r4_repo",
        "private": false,
        "owner": {
          "login": "clark",
          "id": 51,
          "type": "User",
          "site_admin": false
        },
        "html_url": "https://github.com/remote_R4_y",
        "description": "r4 repo",
        "fork": false,
        "created_at": "2020-01-21T17:32:49Z",
        "updated_at": "2020-01-21T17:37:42Z",
        "pushed_at": "2020-01-26T22:35:45Z",
        "homepage": null,
        "size": 3,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": null,
        "has_issues": false,
        "has_projects": true,
        "has_downloads": true,
        "has_wiki": true,
        "has_pages": false,
        "forks_count": 0,
        "mirror_url": null,
        "archived": false,
        "disabled": false,
        "open_issues_count": 1,
        "license": null,
        "forks": 0,
        "open_issues": 1,
        "watchers": 0,
        "default_branch": "master"
      }
    },
    "base": {
      "label": "r4_repo:master",
      "ref": "master",
      "sha": "r4_master_ref",
      "user": {
        "login": "clark",
        "id": 51,
        "type": "User",
        "site_admin": false
      },
      "repo": {
        "id": 115401711,
        "name": "r4_repo",
        "full_name": "proj_name/r4_repo",
        "private": false,
        "owner": {
          "login": "clark",
          "id": 51,
          "type": "User",
          "site_admin": false
        },
        "html_url": "https://localhost/r4_url",
        "description": "r4 repo",
        "fork": false,
        "url": "https://github.com/r4_url",
        "created_at": "2020-01-21T17:32:49Z",
        "updated_at": "2020-01-21T17:37:42Z",
        "pushed_at": "2020-01-26T22:35:45Z",
        "homepage": null,
        "size": 3,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": null,
        "has_issues": false,
        "has_projects": true,
        "has_downloads": true,
        "has_wiki": true,
        "has_pages": false,
        "forks_count": 0,
        "mirror_url": null,
        "archived": false,
        "disabled": false,
        "open_issues_count": 1,
        "license": null,
        "forks": 0,
        "open_issues": 1,
        "watchers": 0,
        "default_branch": "master"
      }
    },
    "_links": {
      "self": {
        "href": "https://github.com/r4_url/pulls/8192"
      },
      "html": {
        "href": "https://localhost/r4_url/pull/8192"
      },
      "issue": {
        "href": "https://github.com/r4_url/issues/8192"
      },
      "comments": {
        "href": "https://github.com/r4_url/issues/8192/comments"
      },
      "review_comments": {
        "href": "https://github.com/r4_url/pulls/8192/comments"
      },
      "review_comment": {
        "href": "https://github.com/r4_url/pulls/comments{/number}"
      },
      "commits": {
        "href": "https://github.com/r4_url/pulls/8192/commits"
      },
      "statuses": {
        "href": "https://github.com/r4_url/statuses/bugfix9_mergeref"
      }
    },
    "author_association": "OWNER",
    "active_lock_reason": null
  }
]
    ''',


        '/repos/r5_url/pulls?state=all': b'''
[
]
        ''',


    '/repos/r6_url/pulls?state=all': b'''
[
  {
    "url": "https://github.com/r6_url/pulls/111",
    "id": 365427119,
    "node_id": "MDExOlB1bGxSZXF1ZXN0MzY1NDI3MjM5",
    "html_url": "https://localhost/r6_url/pull/111",
    "diff_url": "https://localhost/r6_url/pull/111.diff",
    "patch_url": "https://localhost/r6_url/pull/111.patch",
    "issue_url": "https://github.com/r6_url/issues/111",
    "number": 111,
    "state": "open",
    "locked": false,
    "title": "blah match",
    "user": {
      "login": "nick",
      "id": 555,
      "type": "User",
      "site_admin": false
    },
    "body": "",
    "created_at": "2020-01-21T17:35:14Z",
    "updated_at": "2020-01-26T11:35:44Z",
    "closed_at": null,
    "merged_at": null,
    "merge_commit_sha": "r6_blah_merge_commit_ref",
    "assignee": null,
    "assignees": [

    ],
    "requested_reviewers": [

    ],
    "requested_teams": [

    ],
    "labels": [

    ],
    "milestone": null,
    "draft": false,
    "commits_url": "https://github.com/r6_url/pulls/111/commits",
    "review_comments_url": "https://github.com/r6_url/pulls/111/comments",
    "review_comment_url": "https://github.com/r6_url/pulls/comments{/number}",
    "comments_url": "https://github.com/r6_url/issues/111/comments",
    "statuses_url": "https://github.com/r6_url/statuses/blah_mergeref",
    "head": {
      "label": "r6_repo:blah",
      "ref": "blah",
      "sha": "r6_blah_mergeref",
      "user": {
        "login": "nick",
        "id": 555,
        "type": "User",
        "site_admin": false
      },
      "repo": {
        "id": 115401711,
        "name": "r6_repo",
        "full_name": "proj_repo/r6_repo",
        "private": false,
        "owner": {
          "login": "cato",
          "id": 49,
          "type": "User",
          "site_admin": false
        },
        "html_url": "https://github.com/remote_r6_pr111_url",
        "description": "r6 repo",
        "fork": false,
        "created_at": "2020-01-21T17:32:49Z",
        "updated_at": "2020-01-21T17:37:42Z",
        "pushed_at": "2020-01-26T22:35:45Z",
        "homepage": null,
        "size": 3,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": null,
        "has_issues": false,
        "has_projects": true,
        "has_downloads": true,
        "has_wiki": true,
        "has_pages": false,
        "forks_count": 0,
        "mirror_url": null,
        "archived": false,
        "disabled": false,
        "open_issues_count": 1,
        "license": null,
        "forks": 0,
        "open_issues": 1,
        "watchers": 0,
        "default_branch": "master"
      }
    },
    "base": {
      "label": "r6_repo:master",
      "ref": "master",
      "sha": "r6_master_ref",
      "user": {
        "login": "cato",
        "id": 49,
        "type": "User",
        "site_admin": false
      },
      "repo": {
        "id": 115401711,
        "name": "r6_repo",
        "full_name": "proj_name/r6_repo",
        "private": false,
        "owner": {
          "login": "cato",
          "id": 49,
          "type": "User",
          "site_admin": false
        },
        "html_url": "https://localhost/r6_url",
        "description": "r6 repo",
        "fork": false,
        "url": "https://github.com/r6_url",
        "created_at": "2020-01-21T17:32:49Z",
        "updated_at": "2020-01-21T17:37:42Z",
        "pushed_at": "2020-01-26T22:35:45Z",
        "homepage": null,
        "size": 3,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": null,
        "has_issues": false,
        "has_projects": true,
        "has_downloads": true,
        "has_wiki": true,
        "has_pages": false,
        "forks_count": 0,
        "mirror_url": null,
        "archived": false,
        "disabled": false,
        "open_issues_count": 1,
        "license": null,
        "forks": 0,
        "open_issues": 1,
        "watchers": 0,
        "default_branch": "master"
      }
    },
    "_links": {
      "self": {
        "href": "https://github.com/r6_url/pulls/111"
      },
      "html": {
        "href": "https://localhost/r6_url/pull/111"
      },
      "issue": {
        "href": "https://github.com/r6_url/issues/111"
      },
      "comments": {
        "href": "https://github.com/r6_url/issues/111/comments"
      },
      "review_comments": {
        "href": "https://github.com/r6_url/pulls/111/comments"
      },
      "review_comment": {
        "href": "https://github.com/r6_url/pulls/comments{/number}"
      },
      "commits": {
        "href": "https://github.com/r6_url/pulls/111/commits"
      },
      "statuses": {
        "href": "https://github.com/r6_url/statuses/blah_mergeref"
      }
    },
    "author_association": "OWNER",
    "active_lock_reason": null
  }

]
    ''',

    '/repos/r7_url/pulls?state=all': b'''
[
]
        ''',

    '/api/v4/projects/r10_url/merge_requests?scope=all&state=all': b'[]',


    # ############################################################


    '/users/nick' : github_user('https://github.com/r1_url',
                                'nick', 555, 'nick@bad.seeds'),

    '/users/not_nick' : github_user('https://github.com/r1_url',
                                    'not_nick', 554, 'not_nick@bad.seeds'),

    '/users/banana' : github_user('https://github.com/r1_url', 'banana', 553),

    '/users/done' : github_user('https://github.com/r1_url',
                                'done', 552, 'done@already.yo'),

    '/users/ozzie' : github_user('https://github.com/r1_url',
                                 'ozzie', 559, 'ozzie@crazy.train'),



    # ############################################################


    '/repos/r1_url/contents/.gitmodules?ref=master' :
    github_gitmodules_contents('https://github.com/r1_repo', 'master',
                               r1_gitmodules_master),

    '/repos/remote_R1_b/contents/.gitmodules?ref=blah' :
    github_gitmodules_contents('https://github.com/remote_R1_b', 'blah',
                               r1_gitmodules_blah),

    '/repos/r1_url/contents/.gitmodules?ref=feat1' :
        github_gitmodules_contents('https://github.com/r1_repo', 'feat1',
                                   r1_gitmodules_feat1),

    '/repos/r2_url/contents/.gitmodules?ref=master' :
    github_gitmodules_contents('https://github.com/r2_repo', 'master',
                               r2_gitmodules_master),

    '/api/v4/projects/r10_url/repository/files/.gitmodules/raw?ref=master' :
    r10_gitmodules_master,

    '/api/v4/projects/r10_url/repository/files/.gitmodules/raw?ref=devtest' :
    r10_gitmodules_devtest,

    ## deps/r2

    '/repos/r1_url/contents/sub/r2?ref=master' :
    github_submodule_contents('https://github.com/r1_url',
                              'master',
                              'R2',
                              'sub/r2',
                              'r2_master_head',
                              'https://github.com/r2_url'),

    '/repos/remote_R1_b/contents/sub/r2?ref=blah' :
    github_submodule_contents('https://github.com/remote_R1_b',
                              'blah',
                              'R2',
                              'sub/r2',
                              'r2_master_head^22',
                              'https://github.com/r2_url'),


    '/repos/r1_url/contents/sub/r2?ref=feat1' :
    github_submodule_contents('https://github.com/r1_url',
                              'feat1',
                              'R2',
                              'sub/r2',
                              'r2_master_head^1',
                              'https://github.com/r2_url'),

    ## deps/r3

    '/repos/r1_url/contents/sub/r3?ref=master' : b'''
{
  "name": "R3",
  "path": "sub/r3",
  "sha": "r3_master_head^3",
  "size": 0,
  "url": "https://api.github.com/repos/r1_url/contents/deps/r3?ref=master",
  "html_url": "https://github.com/r3_url/tree/r3_master_head^3",
  "git_url": "https://api.github.com/repos/r3_url/git/trees/r3_master_head^3",
  "download_url": null,
  "type": "submodule",
  "submodule_git_url": "https://github.com/r3_url"
}
    ''',

    '/repos/remote_R1_b/contents/sub/r3?ref=blah' : b'''
{
  "name": "R3",
  "path": "sub/r3",
  "sha": "r3_master_head",
  "size": 0,
  "url": "https://api.github.com/repos/remote_R1_b/contents/deps/r3?ref=blah",
  "html_url": "https://github.com/r3_url/tree/r3_master_head",
  "git_url": "https://api.github.com/repos/r3_url/git/trees/r3_master_head",
  "download_url": null,
  "type": "submodule",
  "submodule_git_url": "https://github.com/r3_url"
}
    ''',


    '/repos/r1_url/contents/sub/r3?ref=feat1' : b'''
{
  "name": "R3",
  "path": "sub/r3",
  "sha": "r3_master_head",
  "size": 0,
  "url": "https://api.github.com/repos/r1_url/contents/deps/r3?ref=feat1",
  "html_url": "https://github.com/r3_url/tree/r3_master_head",
  "git_url": "https://api.github.com/repos/r3_url/git/trees/r3_master_head",
  "download_url": null,
  "type": "submodule",
  "submodule_git_url": "https://github.com/r3_url"
}
    ''',


    ## deps/r4

    '/repos/r1_url/contents/deps/r4?ref=master' : b'''
{
  "name": "R4",
  "path": "deps/r4",
  "sha": "r4_master_head^1",
  "size": 0,
  "url": "https://api.github.com/repos/r1_url/contents/deps/r4?ref=master",
  "html_url": "https://github.com/r4_url/tree/r4_master_head^1",
  "git_url": "https://api.github.com/repos/r4_url/git/trees/r4_master_head^1",
  "download_url": null,
  "type": "submodule",
  "submodule_git_url": "https://github.com/r4_url"
}
    ''',

    '/repos/r1_url/contents/deps/r4?ref=feat1' : b'''
{
  "name": "R4",
  "path": "deps/r4",
  "sha": "r4_feat1_head^2",
  "size": 0,
  "url": "https://api.github.com/repos/r1_url/contents/deps/r4?ref=feat1",
  "html_url": "https://github.com/r4_url/tree/r4_feat1_head^2",
  "git_url": "https://api.github.com/repos/r4_url/git/trees/r4_feat1_head^2",
  "download_url": null,
  "type": "submodule",
  "submodule_git_url": "https://github.com/r4_url"
}
    ''',


    ## deps/r7

    '/repos/remote_R1_b/contents/deps/r7?ref=blah' : b'''
{
  "name": "R7",
  "path": "deps/r7",
  "sha": "r7_master_head^4",
  "size": 0,
  "url": "https://api.github.com/repos/remote_R1_b/contents/deps/r7?ref=blah",
  "html_url": "https://github.com/r7_repo/tree/r7_master_head^4",
  "git_url": "https://api.github.com/repos/r7_repo/git/trees/r7_master_head^4",
  "download_url": null,
  "type": "submodule",
  "submodule_git_url": "https://github.com/r7_url"
}
    ''',

    ## deps/r10

    '/api/v4/projects/r10_url/repository/files/sub%2Fr3?ref=master': b'''
{
  "blob_id": "r3_master_head^9",
  "commit_id": "159a7f68667455291637d29afd4fa7a0f3255cf9",
  "content_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "encoding": "base64",
  "file_name": "R3",
  "file_path": "sub/r3",
  "last_commit_id": "c0de6174ade1dc0675076c7683781eed13371934",
  "ref": "master",
  "size": 0
}
    ''',

    '/api/v4/projects/r10_url/repository/files/deps%2Fr4?ref=master': b'''
{
  "blob_id": "r4_master_head^1",
  "commit_id": "159a7f68667455291637d29afd4fa7a0f3255cf9",
  "content_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "encoding": "base64",
  "file_name": "R4",
  "file_path": "deps/r4",
  "last_commit_id": "c0de6174ade1dc0675076c7683781eed13371934",
  "ref": "master",
  "size": 0
}
    ''',

    '/api/v4/projects/r10_url/repository/files/sub%2Fr3?ref=devtest': b'''
{
  "blob_id": "r3_master_head^7",
  "commit_id": "159a7f68667455291637d29afd4fa7a0f3255cfa",
  "content_sha256": "e3b0c44298fc1c149afbf4c8996fb92427af41e4649b934ca495991b7852b855",
  "encoding": "base64",
  "file_name": "R3",
  "file_path": "sub/r3",
  "last_commit_id": "c0de6174ade1dc0675076c7683781eed1337193b",
  "ref": "master",
  "size": 0
}
    ''',

    '/api/v4/projects/r10_url/repository/files/deps%2Fr4?ref=devtest': b'''
{
  "blob_id": "r4_master_head^11",
  "commit_id": "159a7f68667455291637d29afd4fa7a0f3255cfc",
  "content_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4449b934ca495991b7852b855",
  "encoding": "base64",
  "file_name": "R4",
  "file_path": "deps/r4",
  "last_commit_id": "c0de6174ade1dc0675076c7683781eed1337193d",
  "ref": "master",
  "size": 0
}
    ''',

    # ------------------------------------------------------------

    '/repos/r1_url' : b'''
{
  "id": 2431,
  "node_id": "MDEwOlJlchhhaaavcnkyNDMxMjYxMTg=",
  "name": "R1",
  "full_name": "me/R1",
  "private": false,
  "owner": {
    "login": "me",
    "id": 159,
    "node_id": "MDEyOk9yZ2FuaXphdGlvbjE1hohoNzQ=",
    "type": "Organization",
    "site_admin": false
  },
  "html_url": "https://github.com/r1_url",
  "description": "Repo 1 here",
  "fork": false,
  "url": "https://api.github.com/repos/r1_url",
  "created_at": "2020-02-25T23:38:15Z",
  "updated_at": "2020-06-05T04:43:18Z",
  "pushed_at": "2020-06-13T00:16:38Z",
  "homepage": null,
  "size": 1543,
  "stargazers_count": 25,
  "watchers_count": 25,
  "language": "C",
  "has_issues": true,
  "has_projects": true,
  "has_downloads": true,
  "has_wiki": true,
  "has_pages": false,
  "forks_count": 2,
  "mirror_url": null,
  "archived": false,
  "disabled": false,
  "open_issues_count": 18,
  "license": null,
  "forks": 2,
  "open_issues": 18,
  "watchers": 25,
  "default_branch": "master",
  "temp_clone_token": null,
  "organization": {
    "login": "me",
    "id": 159,
    "type": "Organization",
    "site_admin": false
  },
  "network_count": 2,
  "subscribers_count": 27
}
    ''',


    '/repos/remote_R1_b' : b'''
{
  "id": 2432,
  "node_id": "MDEwweJlchhhaaavcnkyNDMxMjYxMTg=",
  "name": "R1_b",
  "full_name": "you/R1_b",
  "private": false,
  "owner": {
    "login": "you",
    "id": 1599,
    "node_id": "MDEyOk9yZ2FuuXphdGlvbjE1hohoNzQ=",
    "type": "Organization",
    "site_admin": false
  },
  "html_url": "https://github.com/remote_R1_b",
  "description": "Repo 1 fork b here",
  "fork": true,
  "url": "https://api.github.com/repos/remote_R1_b",
  "created_at": "2020-02-25T23:38:15Z",
  "updated_at": "2020-06-05T04:43:18Z",
  "pushed_at": "2020-06-13T00:16:38Z",
  "homepage": null,
  "size": 1543,
  "stargazers_count": 25,
  "watchers_count": 25,
  "language": "C",
  "has_issues": true,
  "has_projects": true,
  "has_downloads": true,
  "has_wiki": true,
  "has_pages": false,
  "forks_count": 2,
  "mirror_url": null,
  "archived": false,
  "disabled": false,
  "open_issues_count": 18,
  "license": null,
  "forks": 2,
  "open_issues": 18,
  "watchers": 25,
  "default_branch": "master",
  "temp_clone_token": null,
  "organization": {
    "login": "you",
    "id": 1599,
    "type": "Organization",
    "site_admin": false
  },
  "network_count": 2,
  "subscribers_count": 27
}
    ''',


}


# #######################################################################

forge_stats = {

    'requests': {
        n:(3 if n == '/users/nick' else 1) for n in
        [
            '/repos/r1_url/branches',
            '/repos/r2_url/branches',
            '/repos/r3_url/branches',
            '/repos/r4_url/branches',
            '/repos/r5_url/branches',
            '/repos/r6_url/branches',
            '/repos/r7_url/branches',
            '/repos/r1_url/pulls?state=all',
            '/repos/r2_url/pulls?state=all',
            '/repos/r3_url/pulls?state=all',
            '/repos/r4_url/pulls?state=all',
            '/repos/r5_url/pulls?state=all',
            '/repos/r6_url/pulls?state=all',
            '/repos/r7_url/pulls?state=all',
            '/users/nick',
            '/users/not_nick',
            '/users/banana',
            '/users/done',
            '/users/ozzie',
            '/repos/r1_url/contents/.gitmodules?ref=master',
            '/repos/remote_R1_b/contents/.gitmodules?ref=blah',
            '/repos/r1_url/contents/.gitmodules?ref=feat1',
            '/repos/r1_url/contents/sub/r2?ref=master',
            '/repos/remote_R1_b/contents/sub/r2?ref=blah',
            '/repos/r1_url/contents/sub/r2?ref=feat1',
            '/repos/r1_url/contents/sub/r3?ref=master',
            '/repos/remote_R1_b/contents/sub/r3?ref=blah',
            '/repos/r1_url/contents/sub/r3?ref=feat1',
            '/repos/r1_url/contents/deps/r4?ref=master',
            '/repos/r1_url/contents/deps/r4?ref=feat1',
            '/repos/remote_R1_b/contents/deps/r7?ref=blah',
        ]
    },

    'responses': {
        '/users/nick': [200, 200, 200],
    },

}
