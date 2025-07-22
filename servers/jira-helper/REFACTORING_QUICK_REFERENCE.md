# Refactoring Quick Reference Card

## 🎯 Phase 1 Goals
- **Eliminate 8 instances** of duplicated `_resolve_instance_name()` method
- **Reduce from 9 to 3 services** (JiraService, SearchService, ConfigurationService)
- **Move validation** from domain models to application layer
- **Split 800+ line** infrastructure file into focused components

## 🔧 Key Changes Summary

### Before → After Service Structure
```
BEFORE (9 services):                    AFTER (3 services):
├── IssueService                       ├── JiraService (consolidated)
├── TimeTrackingService                │   ├── Issue operations
├── WorkflowService                    │   ├── Project operations  
├── ProjectService                     │   └── Workflow operations
├── VisualizationService               ├── SearchService (focused)
├── InstanceService                    └── ConfigurationService (consolidated)
├── IssueLinkService                       ├── Instance management
├── IssueUpdateService                     └── Configuration logic
└── SearchService
```

### Code Reduction Targets
| Component | Before | After | Reduction |
|-----------|--------|-------|-----------|
| Service Classes | 9 | 3 | 67% |
| Domain Services File | 1200+ lines | <400 lines | 70% |
| Infrastructure File | 800+ lines | 5 focused files | N/A |
| Duplicated Methods | 8 instances | 0 instances | 100% |

## 📋 Implementation Checklist

### ✅ Task 1.1: BaseJiraService
- [ ] Create `src/domain/base_service.py`
- [ ] Add `_resolve_instance_name()` method
- [ ] Add `_validate_issue_key()` method
- [ ] Add common logging methods
- [ ] Update all 8 services to inherit from base

### ✅ Task 1.2: Consolidate Services
- [ ] Create `src/domain/jira_service.py` (merge 3 services)
- [ ] Extract `src/domain/search_service.py`
- [ ] Create `src/domain/configuration_service.py`
- [ ] Update use cases to use new services
- [ ] Update dependency injection

### ✅ Task 1.3: Simplify Models
- [ ] Create `src/application/validators.py`
- [ ] Remove `@validate_required_fields` decorators
- [ ] Remove business logic methods from models
- [ ] Move validation to application layer

### ✅ Task 1.4: Split Infrastructure
- [ ] Extract `src/infrastructure/atlassian_repository.py`
- [ ] Extract `src/infrastructure/atlassian_link_adapter.py`
- [ ] Extract `src/infrastructure/atlassian_update_adapter.py`
- [ ] Extract `src/infrastructure/atlassian_time_adapter.py`
- [ ] Extract `src/infrastructure/atlassian_search_adapter.py`

## 🚨 Critical Patterns to Follow

### 1. Service Inheritance Pattern
```python
class YourService(BaseJiraService):
    def __init__(self, dependencies...):
        super().__init__(config_provider, logger, **other_deps)
    
    # Remove _resolve_instance_name() - inherited
    # Remove _validate_issue_key() - inherited
    # Keep service-specific methods only
```

### 2. Validation Pattern (Move to Application)
```python
# BEFORE (in domain model):
@validate_required_fields('key', 'summary')
@dataclass
class JiraIssue:
    # ...

# AFTER (in application layer):
class IssueValidator:
    def validate_create_request(self, data: dict) -> list[str]:
        return self.validate_required_fields(data, ['key', 'summary'])
```

### 3. Infrastructure Separation Pattern
```python
# BEFORE (one big file):
class AtlassianApiAdapter:
    # 800+ lines with mixed responsibilities

# AFTER (focused files):
class AtlassianApiRepository:      # Data access only
class AtlassianIssueLinkAdapter:   # Link operations only
class AtlassianTimeTrackingAdapter: # Time tracking only
```

## 🧪 Testing Strategy

### After Each Task
```bash
cd servers/jira-helper
python run_tests.py
```

### Integration Test Points
1. **After Task 1.1**: All services inherit from base, no functionality lost
2. **After Task 1.2**: Service consolidation works, use cases updated
3. **After Task 1.3**: Validation moved, models simplified
4. **After Task 1.4**: Infrastructure split, all adapters work

## ⚠️ Common Pitfalls

### 1. Import Errors
- Update all imports when moving classes
- Check circular dependencies
- Update `__init__.py` files

### 2. Dependency Injection
- Update service factory methods
- Check constructor parameters
- Verify dependency wiring

### 3. Validation Gaps
- Ensure all validation moved to application layer
- No validation logic left in domain models
- Test edge cases thoroughly

### 4. Interface Changes
- Keep public interfaces stable
- Update use cases if service methods change
- Maintain backward compatibility where possible

## 📊 Success Metrics

### Code Quality
- [ ] **Lines of Code**: Reduced by 30-40%
- [ ] **Cyclomatic Complexity**: Domain services <10 per method
- [ ] **File Size**: No file >400 lines
- [ ] **Duplication**: Zero duplicated methods

### Architecture Quality
- [ ] **Dependency Direction**: No infrastructure imports in domain
- [ ] **Single Responsibility**: Each service has one clear purpose
- [ ] **Separation of Concerns**: Validation in application, data in domain

### Performance
- [ ] **Build Time**: Maintained or improved
- [ ] **Test Execution**: <30 seconds total
- [ ] **Memory Usage**: No significant increase

## 🔄 Rollback Plan

### If Issues Arise
1. **Keep original files** until new implementation proven
2. **Use feature flags** for gradual migration
3. **Maintain interface compatibility** during transition
4. **Have comprehensive test suite** before starting

### Emergency Rollback
```bash
# Restore original files
git checkout HEAD~1 -- src/domain/services.py
git checkout HEAD~1 -- src/infrastructure/atlassian_api_adapter.py

# Run tests to verify
python run_tests.py
```

## 📞 Support

### Questions During Implementation
- Check existing architectural review documents
- Refer to hexagonal architecture principles
- Follow DRY/KISS guidelines from core principles
- Test frequently and incrementally

### Code Review Focus Areas
- Service consolidation correctness
- Validation logic completeness  
- Infrastructure separation clarity
- Test coverage maintenance

---

**Quick Start**: Begin with Task 1.1 (BaseJiraService) - it's the foundation for everything else.
**Time Estimate**: 1-2 days per task for experienced developer
**Risk Level**: Low-Medium (internal refactoring, comprehensive tests)
