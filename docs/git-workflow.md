# Git Workflow Documentation

Bu dokümantasyon ArchBuilder.AI projesi için kullanılan GitFlow workflow'unu detaylandırır.

## 🌳 GitFlow Branching Model Overview

ArchBuilder.AI projesi **GitFlow** branching modelini kullanır. Bu model, organize ve güvenli bir geliştirme süreci sağlar.

### Branch Hiyerarşisi

```
main (production)
├── hotfix/123-critical-fix → main + develop
├── release/1.2.0 → main
│
develop (integration)
├── feature/456-new-feature → develop
├── feature/789-improvement → develop
└── bugfix/012-minor-fix → develop
```

## 📊 Branch Types ve Kuralları

### 🏗️ Main Branch
- **Amaç**: Production-ready code
- **Protection**: Admin-only push, PR required
- **Merge Sources**: `release/*`, `hotfix/*` branches only
- **Auto-deployment**: Production environment

### 🔧 Develop Branch  
- **Amaç**: Integration branch for features
- **Protection**: PR required, status checks
- **Merge Sources**: `feature/*`, `bugfix/*`, `main` (hotfix merge-back)
- **Auto-deployment**: Staging environment
- **Default**: New PRs target develop by default

### ✨ Feature Branches
- **Naming**: `feature/123-short-description`
- **Source**: `develop`
- **Target**: `develop`
- **Lifecycle**: Create → Develop → PR → Merge → Delete
- **Protection**: None (temporary branches)

### 🚀 Release Branches
- **Naming**: `release/1.2.0` (SemVer)
- **Source**: `develop`
- **Target**: `main` first, then merge-back to `develop`
- **Purpose**: Version preparation, bug fixes, changelog
- **Protection**: Enhanced review requirements

### 🔥 Hotfix Branches
- **Naming**: `hotfix/123-critical-issue`
- **Source**: `main`
- **Target**: `main` first, then merge-back to `develop`
- **Purpose**: Critical production fixes
- **Priority**: Highest, can interrupt release cycle

### 🐛 Bugfix Branches
- **Naming**: `bugfix/123-bug-description`
- **Source**: `develop`
- **Target**: `develop`
- **Purpose**: Non-critical bug fixes during development

## 🔄 Detailed Workflows

### Feature Development Workflow

```bash
# 1. Start from latest develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/123-add-user-authentication

# 3. Development cycle
# ... make changes ...
git add .
git commit -m "feat(auth): add JWT middleware"

# ... more changes ...
git add .
git commit -m "test(auth): add authentication tests"

# 4. Keep updated with develop
git fetch origin
git rebase origin/develop  # Or merge if preferred

# 5. Push and create PR
git push origin feature/123-add-user-authentication
# Create PR: feature/123-add-user-authentication → develop

# 6. After merge, cleanup
git checkout develop
git pull origin develop
git branch -d feature/123-add-user-authentication
git push origin --delete feature/123-add-user-authentication
```

### Release Workflow

```bash
# 1. Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/1.2.0

# 2. Version preparation
# Update version.md
echo "## 1.2.0 Release - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" >> version.md
echo "- Feature A completed" >> version.md
echo "- Bug fixes applied" >> version.md

# Update package configurations if needed
# Update API documentation
# Run final tests

git add .
git commit -m "chore(release): prepare version 1.2.0"

# 3. Create PR to main
git push origin release/1.2.0
# Create PR: release/1.2.0 → main

# 4. After main merge, tag the release
git checkout main
git pull origin main
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0

# 5. Merge back to develop
git checkout develop
git merge main --no-ff -m "chore: merge release 1.2.0 back to develop"
git push origin develop

# 6. Cleanup release branch
git branch -d release/1.2.0
git push origin --delete release/1.2.0
```

### Hotfix Workflow

```bash
# 1. Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/456-security-vulnerability

# 2. Apply critical fix
# ... make urgent changes ...
git add .
git commit -m "fix(security): resolve authentication bypass issue"

# 3. Create PR to main (high priority)
git push origin hotfix/456-security-vulnerability  
# Create PR: hotfix/456-security-vulnerability → main
# Request immediate review

# 4. After main merge, tag hotfix
git checkout main
git pull origin main
git tag -a v1.1.1 -m "Hotfix version 1.1.1"
git push origin v1.1.1

# 5. Merge back to develop
git checkout develop
git merge main --no-ff -m "chore: merge hotfix 1.1.1 back to develop"
git push origin develop

# 6. Cleanup hotfix branch
git branch -d hotfix/456-security-vulnerability
git push origin --delete hotfix/456-security-vulnerability
```

## 🛡️ Branch Protection Rules

### Main Branch Protection
- ✅ Require PR reviews (1 reviewer minimum)
- ✅ Require status checks: `lint`, `validate`
- ✅ Require up-to-date branches
- ✅ Require conversation resolution
- ✅ Restrict pushes to admins only
- ❌ Allow force pushes
- ❌ Allow deletions

### Develop Branch Protection
- ✅ Require PR reviews (1 reviewer minimum)
- ✅ Require status checks: `lint`, `validate`
- ✅ Require up-to-date branches  
- ✅ Require conversation resolution
- ✅ Allow squash merging only
- ✅ Auto-delete head branches
- ❌ Allow force pushes

## 🔍 Status Checks

### Required Status Checks
All PRs must pass these automated checks:

#### `lint` Check
- Python: Black, isort, flake8, mypy
- .NET: dotnet format
- PowerShell: PSScriptAnalyzer
- Markdown: markdownlint

#### `validate` Check  
- GitFlow branch naming validation
- Registry contract validation
- Context rehydration
- Commit message format (Conventional Commits)
- PR template compliance
- File changes validation
- Dependency security check

## 📝 Commit Message Standards

### Conventional Commits Format
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Commit Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code formatting (no logic change)
- **refactor**: Code refactoring
- **test**: Adding/updating tests
- **chore**: Build process, tools, maintenance

### Examples
```bash
git commit -m "feat(auth): add JWT authentication middleware"
git commit -m "fix(validation): resolve geometry validation edge case"
git commit -m "docs(api): update authentication endpoints documentation"
git commit -m "chore(deps): update fastapi to v0.104.1"
git commit -m "refactor(services): extract validation logic to separate service"
```

## 🚦 PR Guidelines

### PR Naming
PR titles should follow the same format as commit messages:
```
feat(auth): add JWT authentication system
fix(validation): resolve building code compliance issues
```

### PR Template
All PRs must use the provided template including:
- 📋 Description of changes
- 🔗 Related issue link  
- 🏷️ Type of change
- 🧪 Testing information
- 📊 Registry & context impact
- ✅ Comprehensive checklist

### Review Requirements
- **1 reviewer minimum** for all PRs
- **CODEOWNERS review** for critical files
- **Status checks passing** (lint + validate)
- **Conversation resolution** required
- **Up-to-date branch** required

## 🔧 Repository Settings

### Merge Settings
- ✅ **Allow squash merging**: Clean commit history
- ❌ **Allow merge commits**: Disabled for consistency
- ❌ **Allow rebase merging**: Disabled for safety
- ✅ **Automatically delete head branches**: Cleanup

### Default Branch
- **Default branch**: `develop`
- New PRs automatically target `develop`
- New feature branches should be created from `develop`

## 🎯 Best Practices

### Branch Management
1. **Keep branches small**: Focus on single features/fixes
2. **Regular updates**: Rebase/merge with target branch frequently
3. **Descriptive names**: Use issue numbers and clear descriptions
4. **Clean history**: Squash commits in PRs for clean main/develop history

### Development Workflow
1. **Start with issue**: Create GitHub issue for tracking
2. **Update registry**: If adding/changing APIs, update `docs/registry/`
3. **Write tests**: Include tests for new functionality
4. **Update docs**: Add Turkish documentation for user-facing features
5. **Follow instructions**: Adhere to `.github/instructions/` guidelines

### Code Quality
1. **Lint before commit**: Run local linting tools
2. **Test locally**: Ensure tests pass before pushing
3. **Registry validation**: Run `scripts/validate-registry.ps1`
4. **Context rehydration**: Run `scripts/rehydrate-context.ps1`

## 🔍 Troubleshooting

### Common Issues

#### "Branch protection rule violations"
- Ensure you're not pushing directly to `main` or `develop`
- Create a PR instead of direct push
- Check if status checks are passing

#### "Status check failing"
- Run linting tools locally: `black`, `flake8`, `isort`
- Run registry validation: `scripts/validate-registry.ps1`
- Check commit message format
- Ensure PR template is properly filled

#### "Merge conflicts"
- Update your branch with target branch:
  ```bash
  git fetch origin
  git rebase origin/develop  # or origin/main
  ```
- Resolve conflicts and continue rebase
- Force push if necessary: `git push --force-with-lease`

#### "Invalid branch name"
- Use correct GitFlow naming conventions:
  - `feature/123-description`
  - `hotfix/456-critical-fix`
  - `release/1.2.0`
  - `bugfix/789-bug-description`

### Getting Help
1. Check [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines
2. Review [Branch Protection Setup](.mds/BRANCH_PROTECTION_SETUP.md) for admin tasks
3. Create GitHub issue for workflow questions
4. Contact maintainers via PR comments

## 📚 Related Documentation

- [CONTRIBUTING.md](../CONTRIBUTING.md) - Complete contribution guide
- [Branch Protection Setup](.mds/BRANCH_PROTECTION_SETUP.md) - Admin setup guide
- [Registry Governance](docs/registry/README.md) - Registry management
- [Instruction Files](.github/instructions/) - Development guidelines

---

Bu workflow, kod kalitesini ve güvenliği sağlarken, ekip üyelerinin verimli bir şekilde çalışmasını destekler. Herhangi bir sorunuz varsa GitHub Issues üzerinden iletişime geçebilirsiniz.