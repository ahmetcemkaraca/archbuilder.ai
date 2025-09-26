## 📋 Pull Request Description

### 🎯 What does this PR do?
<!-- Briefly describe the changes in this PR -->

### 🔗 Related Issue
<!-- Link to the GitHub issue this PR addresses -->
Closes #<!-- issue number -->

### 🏷️ Type of Change
<!-- Mark the relevant option with [x] -->
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Configuration/tooling change
- [ ] ♻️ Code refactoring
- [ ] 🧪 Test improvements

## 🧪 Testing

### 🔍 How Has This Been Tested?
<!-- Describe the tests you ran to verify your changes -->
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing
- [ ] Registry validation tests

### 🧪 Test Results
```bash
# Paste test results here
```

## 📊 Registry & Context Impact

### 📋 Registry Changes
<!-- Check all that apply -->
- [ ] Updated `docs/registry/identifiers.json`
- [ ] Updated `docs/registry/endpoints.json`
- [ ] Updated `docs/registry/schemas.json`
- [ ] No registry changes needed

### 🔄 Context Management
- [ ] Updated `.mds/context/current-context.md`
- [ ] Context rehydration ran successfully
- [ ] Registry validation passed

### 🗃️ Database Changes
- [ ] Database migrations included
- [ ] Schema changes documented
- [ ] Backward compatibility maintained
- [ ] No database changes

## ✅ Checklist

### 🔧 Code Quality
- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas (in Turkish)
- [ ] Variable names and function names are in English
- [ ] UI text uses i18n (no hardcoded strings)

### 📚 Documentation
- [ ] I have made corresponding changes to the documentation
- [ ] Turkish documentation added for user-facing features
- [ ] API documentation updated if applicable

### 🧪 Testing & Validation
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Registry validation script passes (`scripts/validate-registry.ps1`)
- [ ] Context rehydration script passes (`scripts/rehydrate-context.ps1`)
- [ ] Import checks pass (`pip check` and compilation tests)

### 🔒 Security & Performance
- [ ] I have considered security implications of my changes
- [ ] No sensitive information (passwords, API keys) is hardcoded
- [ ] Performance impact has been considered and documented if significant
- [ ] No SQL injection, XSS, or other security vulnerabilities introduced

### 🌿 GitFlow Compliance
- [ ] Branch follows naming convention (`feature/`, `hotfix/`, `release/`)
- [ ] Targeting correct branch (`develop` for features, `main` for hotfixes)
- [ ] Commits follow conventional commit format
- [ ] No direct commits to protected branches

## 📸 Screenshots (if applicable)
<!-- Add screenshots for UI changes -->

## 🚨 Breaking Changes
<!-- If this is a breaking change, describe what breaks and how to migrate -->

## 📝 Additional Notes
<!-- Any additional information that reviewers should know -->

---

## 👀 For Reviewers

### 🔍 Review Focus Areas
Please pay special attention to:
- [ ] Instruction compliance (`.github/instructions/*.instructions.md`)
- [ ] Registry contract consistency
- [ ] Turkish documentation quality
- [ ] Security implications
- [ ] Performance impact
- [ ] Test coverage

### 🧪 Validation Commands
```bash
# Registry validation
powershell -File scripts/validate-registry.ps1

# Context rehydration
powershell -File scripts/rehydrate-context.ps1

# Import/dependency checks
pip check
python -m py_compile src/cloud-server/app/*.py
```