'''Manages interaction with a Git repository via a forge access,
either as Github or Gitlab.

There are various small differences between the API interactions of
github and gitlab.

Functionally, there are differences between a Github Pull Request
and a Gitlab Merge Request.

 * For a Github Pull request, the PR is an element fetched from the
   main (destination) repository, and the source is identified as a
   specific branch in a separate (forked) repo.

 * For a Gitlab Merge Request, the MR is an element fetched from the
   main (destination) repository, and the source is identified by
   explicit sha reference in a source_project_id, so there is no
   namespace collision concern.

      { "id": 339,
        "project_id": 413,
        "target_branch": "master",
        "source_branch": "master",
        "source_project_id": 414,
        "target_project_id": 413,
        "sha": "33865bc...b1fd8",
        "upvotes": 0,
        "downvotes": 0,
        "work_in_progress": false,
        ...
      }

 * The Gitlab Merge Request may specify either a "source_project_id"
   or a "source_url".

'''

import os
import logging
import hashlib
import subprocess
import requests
import json
from thespian.actors import (ActorTypeDispatcher, ActorSystemMessage, WakeupMessage,
                             ActorExitRequest)
from thespian.initmsgs import initializing_messages
from .ForgeAccess import *
from Briareus.VCS.InternalMessages import *
from Briareus.VCS.GitForge import GitLabInfo, GitHubInfo
import datetime
from typing import (Optional, Union)


def transient_idle(exit_delay=datetime.timedelta(seconds=20)):
    def _TrIdAc(actor_class):
        def rmsg(self, msg, sender):
            if not getattr(self, '_TIES', None):
                self.wakeupAfter(exit_delay)
                self._TIES = datetime.datetime.now() + exit_delay
            if isinstance(msg, WakeupMessage):
                if datetime.datetime.now() >= self._TIES:
                    self.send(self.myAddress, ActorExitRequest())
                else:
                    self.wakeupAfter(self._TIES - datetime.datetime.now())
            elif not isinstance(msg, ActorSystemMessage):
                self._TIES = datetime.datetime.now() + exit_delay
            return self._TIA_rmsg(msg, sender)
        actor_class._TIA_rmsg = actor_class.receiveMessage
        actor_class.receiveMessage = rmsg
        return actor_class
    return _TrIdAc


@initializing_messages([('repospec', RepoRemoteSpec)], init_passthru=True)
@transient_idle(datetime.timedelta(hours=12))
class GitRepoInfo(ActorTypeDispatcher):
    def __init__(self, *args, **kw) -> None:
        super(GitRepoInfo, self).__init__(*args, **kw)
        self._ghinfo: Optional[Union[GitHubInfo, GitLabInfo]] = None
        self.repospec = RepoRemoteSpec(RepoAPI_Location(HTTPS_URL("no-url"), None))

    def receiveMsg_RepoRemoteSpec(self, msg: RepoRemoteSpec, sender) -> None:
        self._ghinfo = (GitHubInfo(msg.repo_api_loc)
                        if 'github' in self.repospec.repo_api_loc.apiloc else
                        (GitLabInfo(msg.repo_api_loc)
                         if 'gitlab' in self.repospec.repo_api_loc.apiloc else
                         None))
        if not self._ghinfo:
            raise ValueError('Cannot determine type of remote repo at %s / %s'
                             % (self.repospec.repo_api_loc.apiloc,
                                msg.repo_api_loc))

    def receiveMsg_GetPullReqs(self, msg: GetPullReqs, sender) -> None:
        # typing ignored because orig_sender dynamically added
        back_to = msg.orig_sender  # type: ignore
        assert self._ghinfo is not None
        try:
            rsp = self._ghinfo.get_pullreqs(msg.reponame)
        except Exception as err:
            logging.critical('GetPullReqs err: %s', err, exc_info=True)
            self.send(back_to,
                      InvalidRepo(msg.reponame, 'git', self.repospec.repo_api_loc.apiloc,
                                  getattr(self._ghinfo, '_url', str(self._ghinfo)),
                                  'GetPullReqs - ' + str(err)))
        else:
            self.send(back_to, rsp)

    def receiveMsg_HasBranch(self, msg: HasBranch, sender) -> None:
        # typing ignored because orig_sender dynamically added
        back_to = msg.orig_sender  # type: ignore
        assert self._ghinfo is not None
        branch = msg.branch_name
        try:
            rsp = self._ghinfo.get_branches()
        except Exception as err:
            logging.critical('HasBranch: %s', err, exc_info=True)
            self.send(back_to,
                      InvalidRepo(msg.reponame, 'git', self.repospec.repo_api_loc.apiloc,
                                  getattr(self._ghinfo, '_url', str(self._ghinfo)),
                                  'HasBranch - ' + str(err)))
        else:
            blist = { b['name']: b['ref'] for b in rsp }
            chk = blist.get(branch, False)
            self.send(back_to,
                      BranchPresent(msg.reponame, branch, chk,
                                    known_branches=list(blist.items())))


    def receiveMsg_GitmodulesData(self, msg: GitmodulesData, sender) -> None:
        # typing ignored because orig_sender dynamically added
        back_to = msg.orig_sender  # type: ignore
        assert self._ghinfo is not None
        branch = msg.branch_name
        try:
            rval = self._ghinfo.get_gitmodules(msg.reponame, branch, msg.pullreq_id)
        except Exception as err:
            logging.critical('GitmodulesData err: %s', err, exc_info=True)
            self.send(back_to,
                      InvalidRepo(msg.reponame, 'git', self.repospec.repo_api_loc.apiloc,
                                  getattr(self._ghinfo, '_url', str(self._ghinfo)),
                                  'GitmodulesData - ' + str(err)))
        else:
            self.send(back_to, rval)


    def receiveMsg_ReadFileFromVCS(self, msg: ReadFileFromVCS, sender) -> None:
        # typing ignored because orig_sender dynamically added
        back_to = msg.orig_sender  # type: ignore
        assert self._ghinfo is not None
        filepath = msg.file_path
        branch = msg.branch or "master"
        try:
            rval = self._ghinfo.get_file_contents_raw(filepath, branch)
        except requests.exceptions.RequestException as err:
            logging.critical('ReadFileFromVCS err: %s', err, exc_info=True)
            if hasattr(err, 'response'):
                ecode = getattr(err.response, 'status_code', -1)
            else:
                ecode = getattr(err, 'errno', -2)
            self.send(back_to, FileReadData(msg.reponame, req=msg, error_code=ecode))
        except Exception as err:
            logging.critical('ReadFileFromVCS err: %s', err, exc_info=True)
            ecode = getattr(err, 'errno', -2)
            self.send(back_to, FileReadData(msg.reponame, req=msg, error_code=ecode))
        else:
            if isinstance(rval, int):
                self.send(back_to, FileReadData(msg.reponame, req=msg, error_code=rval))
            else:
                self.send(back_to, FileReadData(msg.reponame, req=msg, file_data=rval))


    def receiveMsg_str(self, msg: str, sender) -> None:
        if msg == "status":
            self.send(sender, self._ghinfo.stats() if self._ghinfo else
                      { "url": str(self.repospec.repo_api_loc.apiloc) + " (never accessed)",
                      })


