Hi Robin,

Thanks for your response earlier regarding the GitHub Actions settings.

I’m following up on the issue we discussed about exploring solutions to auto-merge PRs in TDU repos. I’ve been encountering some challenges:

1. **API Response Issue**: When trying to implement the automation, the API call response returns a 404 error. I’m not sure if this is related to my PAT not having the correct permissions, or if this functionality is not allowed in our environment.
1. **GitHub Settings**: I noticed that the option in GitHub settings to “Choose whether GitHub Actions can create pull requests or submit approving pull request reviews” is still greyed out. I’m wondering if this is the reason why the automation isn’t working as expected.

As you mentioned, this setting is specifically controlled at the Organization Level Setting. Could you please help me understand:

- Why this setting was turned off in TDU?
- Are there any workflows or documents we can refer to for implementing PR automation in a compliant way?
- Is there any possibility we can do a PoC for mobile teams to test this functionality?

I’ve tried multiple ways to test it out but haven’t had good results so far. Any guidance would be greatly appreciated.

Thank you in advance for your help!

Best regards