# ArchBuilder.AI Branch Integration Roadmap

## 📊 Mevcut Branch Durumu (September 27, 2025)

### Active Branches Analizi
```
develop                                  ✅ 7 commits ahead of main (CURRENT)
├─ feature/7-ai-processing-pipeline      ✅ 5 commits ahead of main 
├─ feature/6-postgresql-connection       ✅ 3 commits ahead of main
├─ feature/deployment-production         ⚠️  4 commits ahead of main (diverged)
└─ docs/update-project-structure         ❌ 14 commits behind main (STALE)
```

### Branch Durumu Detay
| Branch | Ahead/Behind | Last Commit | Status | Integration Risk |
|--------|--------------|-------------|--------|------------------|
| `develop` | +7/0 | 51 sec ago | ✅ Current | LOW - Clean merge |
| `feature/7-ai-processing-pipeline` | +5/0 | 50 min ago | ✅ Active | LOW - Direct ancestor |
| `feature/6-postgresql-connection` | +3/0 | 18 hours ago | ✅ Ready | LOW - Direct ancestor |
| `feature/deployment-production` | +4/0 | 18 hours ago | ⚠️ Diverged | MEDIUM - Needs rebase |
| `docs/update-project-structure` | 0/14 | 3 days ago | ❌ Stale | HIGH - Outdated |

## 🚀 Integration Strategy (Recommended Order)

### Phase 1: Clean Merges (1-2 days)
**Priority: HIGH - No conflicts expected**

1. **`feature/6-postgresql-connection-optimization`** ✅
   ```bash
   git checkout main
   git pull origin main
   git merge feature/6-postgresql-connection-optimization
   git push origin main
   ```
   - **Content**: PostgreSQL connection pool optimization
   - **Risk**: LOW - Database optimization, no UI conflicts
   - **Tests**: Ensure connection pool tests pass

2. **`feature/7-ai-processing-pipeline-completion`** ✅  
   ```bash
   git checkout main
   git merge feature/7-ai-processing-pipeline-completion
   git push origin main
   ```
   - **Content**: AI processing pipeline, Revit API validation
   - **Risk**: LOW - Clean ancestor relationship with develop
   - **Tests**: Validate AI integration tests

### Phase 2: Current Prompt System (Same day)
**Priority: HIGH - Latest improvements**

3. **`develop` (Prompt System Reorganization)** ✅
   ```bash
   git checkout main  
   git merge develop
   git push origin main
   ```
   - **Content**: Complete prompt system reorganization + /todogorev automation
   - **Risk**: LOW - Latest changes, documentation focused
   - **Tests**: Validate prompt system functionality

### Phase 3: Conflict Resolution (2-3 days)
**Priority: MEDIUM - Requires attention**

4. **`feature/deployment-production-readiness`** ⚠️
   ```bash
   # Rebase yaklaşımı (önerilen)
   git checkout feature/deployment-production-readiness
   git rebase main
   # Conflicts varsa çöz
   git rebase --continue
   git checkout main
   git merge feature/deployment-production-readiness
   git push origin main
   ```
   - **Content**: Production deployment configurations
   - **Risk**: MEDIUM - GitFlow workflow changes, may conflict
   - **Manual Review**: Instruction file conflicts possible

### Phase 4: Stale Branch Cleanup
**Priority: LOW - Archive or recreate**

5. **`docs/update-project-structure-website-removal`** ❌
   ```bash
   # Option A: Archive (önerilen)
   git branch -m docs/update-project-structure-website-removal archive/docs-project-structure-old
   
   # Option B: Recreate if needed
   git checkout main
   git checkout -b docs/update-project-structure-new
   # Manually apply needed changes
   ```
   - **Content**: Project structure updates, website removal
   - **Risk**: HIGH - 14 commits behind, major conflicts expected
   - **Recommendation**: Archive and recreate if needed

## 🔧 Pre-Integration Checklist

### Before Each Merge
- [ ] **Backup current state**: `git tag backup-pre-merge-$(date +%Y%m%d-%H%M)`
- [ ] **Run tests**: Ensure branch tests pass locally
- [ ] **Check conflicts**: `git merge --no-commit --no-ff target-branch`
- [ ] **Validate imports**: Ensure all Python imports resolve
- [ ] **Registry sync**: Update docs/registry/*.json if needed

### Integration Commands Template
```powershell
# 1. Prepare main branch
git checkout main
git pull origin main
git tag backup-integration-$(Get-Date -Format "yyyyMMdd-HHmm")

# 2. Test merge (dry run)
git merge --no-commit --no-ff feature/branch-name
git merge --abort  # if no conflicts, proceed

# 3. Actual merge
git merge feature/branch-name
git push origin main

# 4. Cleanup
git branch -d feature/branch-name
git push origin --delete feature/branch-name
```

## 🚨 Risk Mitigation

### High-Risk Scenarios
1. **File Conflicts**: Especially in `.github/instructions/` and `src/cloud-server/`
2. **Import Issues**: New dependencies may break existing code
3. **Registry Inconsistencies**: Contract changes may not be synchronized

### Rollback Strategy
```powershell
# Quick rollback if integration fails
git reset --hard backup-integration-YYYYMMDD-HHMM
git push origin main --force-with-lease

# Or revert specific merge
git revert -m 1 <merge-commit-hash>
git push origin main
```

## 📋 Post-Integration Tasks

### After Each Successful Merge
- [ ] **Update TODO.md**: Mark completed tasks
- [ ] **Run full test suite**: Ensure system integrity  
- [ ] **Update documentation**: Reflect merged changes
- [ ] **Validate /todogorev**: Test new prompt system functionality
- [ ] **Registry validation**: Run `pwsh -File scripts/validate-registry.ps1`

### Final Integration Validation
- [ ] **Full system test**: Desktop + Cloud + Revit integration
- [ ] **AI functionality**: Test OpenAI/Azure OpenAI/Vertex AI connections
- [ ] **Performance benchmarks**: Ensure no regressions
- [ ] **Security scan**: Validate dependencies and configurations

## 🎯 Expected Timeline

- **Week 1 (Oct 1-3)**: Phases 1-2 (Clean merges + Current develop)
- **Week 2 (Oct 4-6)**: Phase 3 (Conflict resolution)
- **Week 3 (Oct 7-9)**: Phase 4 (Cleanup + validation)
- **Week 4 (Oct 10-12)**: Final testing and documentation

## ⚡ Quick Start Commands

```powershell
# Start integration process
cd C:\Users\ahmet\Desktop\app\archbuilder.aiV2

# Phase 1: PostgreSQL optimization
git checkout main
git pull origin main
git merge feature/6-postgresql-connection-optimization
git push origin main

# Phase 1: AI pipeline 
git merge feature/7-ai-processing-pipeline-completion
git push origin main

# Phase 2: Prompt system (current develop)
git merge develop
git push origin main

# Test everything
npm test # if applicable
python -m pytest src/cloud-server/tests/
pwsh -File scripts/validate-registry.ps1
```

---

**Issue**: https://github.com/ahmetcemkaraca/archbuilder.ai/issues/1
**Status**: Ready for systematic integration
**Next Action**: Begin Phase 1 with PostgreSQL optimization merge