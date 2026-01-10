# ARCHIVIT UX Commandments

**CRITICAL: All agents and developers must follow these principles.**

## The Anti-Patterns We REFUSE to Repeat

### 1. NO Hidden "..." Menus
- Every action should be visible or clearly labeled
- If there are multiple actions, show them or use a clearly labeled dropdown ("Actions", "More Options")
- Never hide critical functions behind mystery icons

### 2. NO Settings Buried in Settings
- One Settings location, not "Project Settings" vs "Service Settings" vs "Account Settings"
- If settings exist, they're findable in ONE place

### 3. NO Hunting for DNS/Domains/Networking
- Connection and sharing options should be obvious
- "Share" or "Publish" should be a primary action, not buried

### 4. NO Ambiguous State
- User should always know: Is this working? Is this broken? Is this loading?
- Clear status indicators, not mystery icons with numbers

### 5. NO Platform-Specific Knowledge Required
- User shouldn't need to know what a "CNAME" is
- User shouldn't need to know what a "Procfile" is
- Abstract the infrastructure completely

### 6. Consistent Menu Structure
- Same patterns across all screens
- If navigation is on the left on one screen, it's on the left everywhere
- If actions are at the top on one screen, they're at the top everywhere

### 7. Errors That Humans Understand
- Not "502 Bad Gateway"
- Instead: "The app couldn't start. Here's what went wrong: [X]. To fix it: [Y]"

### 8. No Account Creation for Basic Actions
- View something? No account needed.
- One-time action? No account needed.
- Ongoing relationship? OK, maybe an account.

## The Standard We're Setting

If a user (non-technical artist) can't figure out how to do something in under 30 seconds, the UI has failed. Not the user.

## Version Control for Humans

Users need to browse and restore previous versions without technical knowledge:
- Visual timeline of changes
- One-click preview of any version
- One-click restore
- No git/terminal required
- Automatic snapshots on meaningful changes

This is a STARG8 core feature requirement.

---

## Menu Consistency Checklist (Pre-Launch)

- [ ] Audit all screens for "..." hidden menus - eliminate or replace with labeled buttons
- [ ] Verify settings are in ONE location
- [ ] Test with non-technical user (30-second rule)
- [ ] All error messages reviewed for human readability
- [ ] Navigation consistent across all views

---

*Added: 2026-01-10*
*Context: Frustration with Railway/Wix hidden menus during deployment*
*This is a reminder of WHY we're building STARG8 - to eliminate this chaos*
