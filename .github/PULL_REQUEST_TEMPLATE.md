<!-- 
ArchBuilder.AI Pull Request Template
Please fill out this template to help reviewers understand your changes.
-->

## 📋 Pull Request Checklist

### Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] 🧪 Test improvements
- [ ] 🔒 Security enhancement

### Description
**What does this PR do?**
<!-- Provide a clear and concise description of what this PR accomplishes -->

**Why is this change needed?**
<!-- Explain the problem this PR solves or the feature it adds -->

**How has this been tested?**
<!-- Describe the tests you ran to verify your changes -->

### 🔗 Related Issues
- Closes #<!-- issue number -->
- Related to #<!-- issue number -->

### 🧪 Testing
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have tested this change manually

### 📚 Documentation
- [ ] I have updated the documentation accordingly
- [ ] I have commented my code, particularly in hard-to-understand areas (in English)
- [ ] I have updated the CHANGELOG.md if applicable

### 🔒 Security
- [ ] I have considered security implications of this change
- [ ] I have run security scans if applicable
- [ ] I have not introduced any hardcoded secrets or credentials

### 📈 Performance
- [ ] I have considered the performance impact of this change
- [ ] I have optimized queries/algorithms where applicable
- [ ] I have not introduced memory leaks or performance regressions

### 🌍 Internationalization
- [ ] I have used i18n for all user-facing text (no hardcoded strings)
- [ ] I have added translation keys to all supported languages
- [ ] UI text follows the English-first, Turkish-supported pattern

### 🎯 Code Quality
- [ ] My code follows the established code style
- [ ] I have performed a self-review of my own code
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have followed GitFlow branching strategy

### 📊 Registry Updates
- [ ] I have updated `docs/registry/identifiers.json` for new modules/exports
- [ ] I have updated `docs/registry/endpoints.json` for API changes
- [ ] I have updated `docs/registry/schemas.json` for data model changes
- [ ] I have updated `.mds/context/current-context.md` if needed

### 🚀 Deployment
- [ ] This change is backward compatible OR I have a migration plan
- [ ] I have considered the rollback strategy
- [ ] I have updated deployment documentation if needed
- [ ] Environment variables are documented in `.env.example`

## 📸 Screenshots (if applicable)
<!-- Add screenshots to help explain your changes -->

## 📝 Additional Notes
<!-- Add any additional notes, concerns, or explanations here -->

## 🎯 Review Focus Areas
<!-- Highlight specific areas where you'd like reviewer attention -->
- [ ] Security implications
- [ ] Performance considerations  
- [ ] Error handling
- [ ] Test coverage
- [ ] Documentation completeness

---

**Reviewer Guidelines:**
- Check for security vulnerabilities
- Verify test coverage is adequate
- Ensure documentation is updated
- Confirm registry files are updated for contract changes
- Validate i18n implementation for UI changes