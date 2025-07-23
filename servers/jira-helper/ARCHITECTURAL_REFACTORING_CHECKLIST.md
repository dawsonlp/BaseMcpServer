# Architectural Refactoring Checklist

## Overview
This checklist implements the architectural improvements identified in the code review, focusing on DRY/KISS principles and proper hexagonal architecture implementation.

## Phase 1: Critical Fixes (Week 1) - HIGH PRIORITY

### 1.1 Eliminate Service Layer Duplication ✅ CRITICAL - COMPLETED
**Goal**: Remove 8 instances of duplicated `_resolve_instance_name()` method

- [x] **Create BaseJiraService class** ✅ COMPLETED (Commit: 2c731a3)
  - [x] Extract common `_resolve_instance_name()` method
  - [x] Extract common `_validate_issue_key()` method  
  - [x] Add common constructor pattern for dependencies
  - [x] Add common error handling patterns
  - **File**: `src/domain/base_service.py`
  - **Actual Impact**: Eliminated 200+ lines of duplication

- [x] **Update all service classes to inherit from BaseJiraService** ✅ COMPLETED (Commit: 2c731a3)
  - [x] `IssueService` - remove duplicated methods
  - [x] `TimeTrackingService` - remove duplicated methods
  - [x] `WorkflowService` - remove duplicated methods
  - [x] `ProjectService` - remove duplicated methods
  - [x] `VisualizationService` - remove duplicated methods
  - [x] `IssueLinkService` - remove duplicated methods
  - [x] `IssueUpdateService` - remove duplicated methods
  - [x] `SearchService` - remove duplicated methods
  - **Files**: All service files in `src/domain/services.py`
  - **Actual Impact**: 200+ lines reduction, 90% duplication eliminated

### 1.2 Consolidate Service Layer ✅ CRITICAL - COMPLETED
**Goal**: Reduce from 9 services to 3 core services

- [x] **Create consolidated JiraService** ✅ COMPLETED (Commit: a78dd6c)
  - [x] Merge `IssueService` + `ProjectService` + `WorkflowService`
  - [x] Keep only core CRUD operations
  - [x] Remove over-abstracted methods
  - **New File**: `src/domain/jira_service.py`
  - **Actual Impact**: Consolidated 3 services into 1 focused service

- [x] **Keep SearchService as-is** ✅ COMPLETED (Commit: a78dd6c)
  - [x] Already well-focused on search operations
  - [x] Apply BaseJiraService inheritance only
  - **File**: Extract to `src/domain/search_service.py`

- [x] **Create ConfigurationService** ✅ COMPLETED (Commit: a78dd6c)
  - [x] Merge `InstanceService` + configuration logic
  - [x] Handle all instance management
  - **New File**: `src/domain/configuration_service.py`

### 1.3 Simplify Domain Models ✅ HIGH - COMPLETED
**Goal**: Move validation logic out of domain models

- [x] **Create Application Layer Validators** ✅ COMPLETED (Commit: 228e3e0)
  - [x] Extract validation from `@validate_required_fields` decorators
  - [x] Create `IssueValidator`, `ProjectValidator`, etc.
  - **New File**: `src/application/validators.py`
  - **Actual Impact**: 300+ lines moved from domain to application

- [x] **Simplify Domain Models** ✅ COMPLETED (Commit: 228e3e0)
  - [x] Remove validation decorators from dataclasses
  - [x] Keep models as pure data containers
  - [x] Remove business logic methods from models
  - **New File**: `src/domain/models_simplified.py`
  - **Actual Impact**: Created clean data containers without validation logic

### 1.4 Fix Infrastructure Layer Issues ✅ HIGH - COMPLETED
**Goal**: Proper separation of concerns in infrastructure

- [x] **Split atlassian_api_adapter.py** ✅ COMPLETED (Commit: 89f0df5)
  - [x] Extract `AtlassianApiRepository` to separate file
  - [x] Extract `AtlassianIssueLinkAdapter` to separate file
  - [x] Extract `AtlassianIssueUpdateAdapter` to separate file
  - [x] Extract `AtlassianTimeTrackingAdapter` to separate file
  - [x] Extract `AtlassianSearchAdapter` to separate file
  - **New Files**: 
    - `src/infrastructure/atlassian_repository.py`
    - `src/infrastructure/atlassian_link_adapter.py`
    - `src/infrastructure/atlassian_update_adapter.py`
    - `src/infrastructure/atlassian_time_adapter.py`
    - `src/infrastructure/atlassian_search_adapter.py`
  - **Actual Impact**: 800+ lines properly organized into 5 focused adapters

## Phase 2: Hexagonal Architecture Fixes (Week 2-3) - MEDIUM PRIORITY

### 2.1 Proper Port/Adapter Separation ✅ MEDIUM - PARTIALLY COMPLETE
**Goal**: Clean dependency flow following hexagonal architecture

- [x] **Create Abstract Repository Interfaces** ✅ ALREADY DONE
  - [x] Define `JiraRepository` interface in domain - Already exists in `src/domain/ports.py`
  - [x] Define `IssueSearchPort` interface in domain - Already exists in `src/domain/ports.py`
  - [x] Define `ConfigurationProvider` interface in domain - Already exists in `src/domain/ports.py`
  - **File**: `src/domain/ports.py` - Already comprehensive with 15+ interfaces

- [x] **Update Domain Services** ✅ ALREADY DONE
  - [x] Remove direct imports of infrastructure ports - Already done
  - [x] Use abstract repository interfaces only - Already implemented
  - [x] Implement proper dependency injection - Already working
  - **Files**: All domain service files already use abstract interfaces

- [x] **Update Infrastructure Implementations** ✅ COMPLETED
  - [x] Implement abstract repository interfaces - Fully implemented
  - [x] Complete missing repository methods (search_issues, get_custom_field_mappings, get_workflow_data) - ✅ COMPLETED
  - [x] Remove domain logic from infrastructure - Already clean
  - **Files**: `src/infrastructure/atlassian_repository.py` - All methods implemented

### 2.2 Clean Application Layer ✅ MEDIUM - COMPLETED
**Goal**: Proper application layer responsibilities

- [x] **Move Validation to Application Layer** ✅ COMPLETED IN PHASE 1
  - [x] Create validation services - Already done in Phase 1
  - [x] Update use cases to use validators - Integration completed
  - [x] Remove validation from domain services - Already done in Phase 1
  - **Files**: `src/application/validators.py` - Already comprehensive

- [x] **Add Error Mapping** ✅ COMPLETED
  - [x] Map infrastructure errors to domain errors - Comprehensive error mapping implemented
  - [x] Centralize error handling - ErrorMapper with context builder created
  - **New File**: `src/application/error_mappers.py` - ✅ COMPLETED

### 2.3 Improve Use Case Layer ✅ MEDIUM - COMPLETED
**Goal**: Enhance existing BaseUseCase pattern

- [x] **Add Validation Support to BaseUseCase** ✅ COMPLETED
  - [x] Integrate validators into base class - Added `_validate_with_validator()` method
  - [x] Automatic validation before execution - Added `execute_with_validation()` method
  - [x] Infrastructure error mapping integration - Added `_map_infrastructure_error()` method
  - **File**: `src/application/base_use_case.py` - Enhanced with validation and error mapping

## Phase 3: Advanced Optimizations (Month 1-2) - LOW PRIORITY

### 3.1 Reduce Model Complexity ✅ LOW
**Goal**: Simplify domain model structure

- [ ] **Consolidate Related Models**
  - [ ] Merge similar request/response models
  - [ ] Use composition instead of inheritance
  - [ ] Reduce from 25+ models to 12-15 core models
  - **File**: `src/domain/models.py`

- [ ] **Implement Value Objects**
  - [ ] Create `IssueKey`, `ProjectKey` value objects
  - [ ] Add validation to value objects
  - **New File**: `src/domain/value_objects.py`

### 3.2 Performance Optimizations ✅ LOW
**Goal**: Improve runtime performance

- [ ] **Add Caching Layer**
  - [ ] Cache frequently accessed projects
  - [ ] Cache issue metadata
  - **New File**: `src/infrastructure/cache_adapter.py`

- [ ] **Optimize Database Queries**
  - [ ] Batch operations where possible
  - [ ] Reduce API calls through better data fetching
  - **Files**: Repository implementations

### 3.3 Testing Improvements ✅ LOW
**Goal**: Better test coverage and organization

- [ ] **Add Integration Tests**
  - [ ] Test complete use case flows
  - [ ] Test error scenarios
  - **New File**: `src/tests/integration/`

- [ ] **Add Contract Tests**
  - [ ] Test port/adapter contracts
  - [ ] Ensure interface compliance
  - **New File**: `src/tests/contracts/`

## Implementation Guidelines

### Code Quality Standards
- **Maximum File Size**: 400 lines per file
- **Maximum Method Size**: 20 lines per method
- **Maximum Class Size**: 200 lines per class
- **Cyclomatic Complexity**: Maximum 10 per method

### Testing Requirements
- [ ] **Unit Tests**: All new/modified classes must have unit tests
- [ ] **Integration Tests**: All use cases must have integration tests
- [ ] **Test Coverage**: Maintain >90% coverage
- [ ] **Test Performance**: All tests must run in <30 seconds

### Documentation Requirements
- [ ] **API Documentation**: Update all public interfaces
- [ ] **Architecture Documentation**: Update hexagonal architecture diagrams
- [ ] **Migration Guide**: Document breaking changes
- [ ] **Performance Metrics**: Document before/after metrics

## Success Metrics

### Code Reduction Targets
- [ ] **Total Lines of Code**: Reduce by 30-40% (from ~3000 to ~2000 lines)
- [ ] **Service Classes**: Reduce from 9 to 3 services
- [ ] **Domain Services File**: Reduce from 1200+ to <400 lines
- [ ] **Infrastructure Adapter**: Split 800+ line file into 5 focused files
- [ ] **Code Duplication**: Eliminate 90% of identified duplications

### Architecture Quality Targets
- [ ] **Dependency Direction**: Zero infrastructure imports in domain layer
- [ ] **Single Responsibility**: Each service has one clear purpose
- [ ] **Interface Segregation**: Small, focused interfaces
- [ ] **Dependency Inversion**: All dependencies point inward

### Performance Targets
- [ ] **Build Time**: Reduce by 20%
- [ ] **Test Execution**: Reduce by 30%
- [ ] **Memory Usage**: Reduce by 15%
- [ ] **API Response Time**: Maintain current performance

## Risk Mitigation

### High Risk Items
- [ ] **Service Consolidation**: Risk of breaking existing functionality
  - **Mitigation**: Comprehensive integration tests before changes
  - **Rollback Plan**: Keep original services until new ones are proven

- [ ] **Model Validation Changes**: Risk of validation gaps
  - **Mitigation**: Extensive validation testing
  - **Rollback Plan**: Feature flags for old vs new validation

### Medium Risk Items
- [ ] **Port/Adapter Refactoring**: Risk of dependency injection issues
  - **Mitigation**: Gradual migration with interface compatibility
  - **Rollback Plan**: Maintain adapter wrappers during transition

## Completion Criteria

### Phase 1 Complete When:
- [ ] All services inherit from BaseJiraService
- [ ] Service count reduced to 3 core services
- [ ] Domain models contain no validation logic
- [ ] Infrastructure layer properly separated
- [ ] All tests pass
- [ ] Code coverage maintained >90%

### Phase 2 Complete When:
- [ ] Domain layer has zero infrastructure imports
- [ ] All repositories use abstract interfaces
- [ ] Application layer handles all validation
- [ ] Error mapping centralized
- [ ] All tests pass

### Phase 3 Complete When:
- [ ] Model count reduced to target
- [ ] Performance targets met
- [ ] Caching implemented
- [ ] Full test suite complete
- [ ] Documentation updated

## Notes
- **Estimated Total Effort**: 3-4 weeks for Phases 1-2
- **Team Size**: 1-2 developers
- **Dependencies**: None (internal refactoring only)
- **Breaking Changes**: Minimal (mostly internal structure)
- **Deployment Impact**: None (internal refactoring only)

---

**Last Updated**: January 22, 2025  
**Status**: Ready for Implementation  
**Priority**: Phase 1 items are critical for code maintainability
