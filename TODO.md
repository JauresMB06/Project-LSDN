# API Error Fix - 422 Unprocessable Entity

## Problem
- Frontend form was sending extra fields (species, region, affectedCount, priority, notes) that backend ReportRequest model doesn't accept
- Missing required reporter_id field in the form

## Changes Made
- [x] Added reporterId field to form schema with validation
- [x] Updated form default values to include reporterId
- [x] Modified onSubmit to only send backend-expected fields: disease_name, location, reporter_id, mortality_count
- [x] Updated form validation to include reporterId in step 2
- [x] Added reporterId input field to step 2 form UI

## Testing Needed
- [ ] Test form submission with valid reporter ID
- [ ] Verify no more 422 errors
- [ ] Check that report is successfully submitted to backend

## Files Modified
- frontend/components/report-disease-modal.tsx
