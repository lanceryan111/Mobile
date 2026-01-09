Hi Soft Token team,

I would like to propose that we take a look at the Gitflow branch strategy (link below), which is widely adopted in financial institutions. Given our recent workflow discussions, it may be helpful to review this model internally and assess whether parts of it could improve our current process.

Reference: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow

Below are several benefits typically associated with Gitflow:

1. Structured Branching Model: Clear roles for branches (e.g., master, develop, release, and hotfix) help streamline change management.
2. Parallel Development: Multiple feature efforts can proceed concurrently without blocking or interfering with each other.
3. Stable Releases: Release branches support final testing and bug fixing before merging into master, ensuring consistent production deployments.
4. Faster Production Fixes: Hotfix branches allow production issues to be addressed quickly while ongoing development continues.
5. Clear Commit History: The structured workflow helps maintain an organized history, making tracking and audits easier.
6. Team Collaboration: Provides a predictable model for integration and testing, improving coordination across contributors.

If the team is open to it, we can schedule a short discussion to evaluate whether adopting elements of this approach would bring value to our Soft Token workflow.

Thanks,  
Fei