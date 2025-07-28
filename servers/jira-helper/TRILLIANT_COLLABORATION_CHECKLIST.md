# Custom Fields Support Enhancement Checklist

## Overview
Adding custom fields support to jira-helper MCP server to enable ticket creation in projects that require custom fields (e.g., "Roadmap Project").

## Branch: `feature/custom-fields-support`

## Completed Tasks ✅

### Phase 1: Custom Field Mappings Fix
- [x] **Fixed CustomFieldMapping constructor error** - Changed `field_name` parameter to `name` in `AtlassianApiRepository.get_custom_field_mappings()`
- [x] **Tested custom field mappings retrieval** - Verified both `reverse: true` and `reverse: false` work correctly
- [x] **Redeployed server** - Used `mcp-manager install local jira-helper --source servers/jira-helper --force --pipx`

## In Progress Tasks 🔄

### Phase 2: Custom Fields Support for Issue Creation
- [ ] **Domain Model Enhancement**
  - [ ] Add `custom_fields: dict[str, Any]` parameter to `IssueCreateRequest` dataclass
  - [ ] Add validation for custom field structure
  - [ ] Maintain backward compatibility

- [ ] **Repository Layer Integration**
  - [ ] Modify `AtlassianApiRepository.create_issue()` to merge custom fields into Jira API payload
  - [ ] Test custom field integration with Jira API
  - [ ] Preserve existing field handling (priority, assignee, labels)

- [ ] **Use Case Layer Updates**
  - [ ] Update `CreateIssueUseCase.execute()` to accept `custom_fields` parameter
  - [ ] Update `CreateIssueWithLinksUseCase.execute()` to accept `custom_fields` parameter
  - [ ] Pass custom fields through to `IssueCreateRequest`

- [ ] **Testing & Validation**
  - [ ] Test with US60 project and "Roadmap Project" custom field
  - [ ] Verify backward compatibility with existing calls
  - [ ] Test both `create_jira_ticket` and `create_issue_with_links` tools

- [ ] **Deployment**
  - [ ] Redeploy server with mcp-manager
  - [ ] Verify tools expose new `custom_fields` parameter
  - [ ] Test end-to-end ticket creation in US60 project

## Pending Tasks 📋

### Phase 3: Documentation & Cleanup
- [ ] **Update Documentation**
  - [ ] Update tool descriptions to mention custom fields support
  - [ ] Add usage examples to README
  - [ ] Document custom field format requirements

- [ ] **Code Review & Cleanup**
  - [ ] Review all changes for architecture compliance
  - [ ] Ensure proper error handling for invalid custom fields
  - [ ] Add unit tests for new functionality

## Technical Notes

### Custom Field Format
```python
custom_fields = {
    "customfield_12259": {"value": "Unitysuite60", "id": "13099"}  # Roadmap Project
}
```

### Architecture Compliance
- ✅ Follows hexagonal architecture patterns
- ✅ Maintains clean separation of concerns
- ✅ Leverages existing bulk registration system
- ✅ Preserves backward compatibility

### Files Modified
- `servers/jira-helper/src/infrastructure/atlassian_repository.py` (Phase 1 ✅)
- `servers/jira-helper/src/domain/models.py` (Phase 2 - Pending)
- `servers/jira-helper/src/application/use_cases.py` (Phase 2 - Pending)

## Testing Strategy

### Test Cases
1. **Backward Compatibility**: Existing calls without custom_fields continue to work
2. **Custom Fields Integration**: New calls with custom_fields create tickets successfully
3. **US60 Project**: Specific test with "Roadmap Project" custom field
4. **Error Handling**: Invalid custom field formats are handled gracefully
5. **Both Tools**: Test both `create_jira_ticket` and `create_issue_with_links`

### Test Data
```python
# US60 Roadmap Project custom field
test_custom_fields = {
    "customfield_12259": {"value": "Unitysuite60", "id": "13099"}
}
```

## Success Criteria
- [x] Custom field mappings retrieval works correctly
- [ ] Can create tickets in US60 project with required custom fields
- [ ] Existing functionality remains unaffected
- [ ] Both MCP tools expose and handle custom_fields parameter
- [ ] Error messages are clear and helpful for invalid custom fields

---
**Last Updated**: January 28, 2025 11:38 AM
**Status**: Phase 1 Complete ✅, Phase 2 In Progress 🔄
