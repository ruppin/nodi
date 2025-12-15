# JSON Filtering in Nodi

## Overview

Nodi supports jq-style filtering for API responses. Filters allow you to extract specific data from JSON responses without needing external tools.

## Syntax

Filters are added to requests using the pipe (`|`) operator:

```bash
<request> | <filter>
```

## Supported Filter Expressions

### Identity and Basic Access

| Filter | Description | Example Input | Example Output |
|--------|-------------|---------------|----------------|
| `.` | Identity (returns entire object) | `{"name": "John"}` | `{"name": "John"}` |
| `.field` | Get field value | `{"name": "John"}` | `"John"` |
| `.field.nested` | Nested field access | `{"user": {"name": "John"}}` | `"John"` |

### Array Operations

| Filter | Description | Example Input | Example Output |
|--------|-------------|---------------|----------------|
| `.[]` | Iterate/expand array | `[1, 2, 3]` | `[1, 2, 3]` |
| `.[n]` | Get array element by index | `[1, 2, 3]` with `.[0]` | `1` |
| `.[n].field` | Get field from array element | `[{"id": 1}, {"id": 2}]` with `.[0].id` | `1` |

### Array Expansion with Field Access

| Filter | Description | Example Input | Example Output |
|--------|-------------|---------------|----------------|
| `.[*].field` | Map field from all array elements | `[{"id": 1}, {"id": 2}]` | `[1, 2]` |
| `.[].field` | Same as `.[*].field` | `[{"id": 1}, {"id": 2}]` | `[1, 2]` |
| `.[*].field.nested` | Map nested field from array | `[{"user": {"name": "John"}}]` | `["John"]` |

### Utility Functions

| Filter | Description | Example Input | Example Output |
|--------|-------------|---------------|----------------|
| `length` | Get length of array/object/string | `[1, 2, 3]` | `3` |
| `keys` | Get sorted object keys | `{"b": 2, "a": 1}` | `["a", "b"]` |
| `values` | Get object values | `{"a": 1, "b": 2}` | `[1, 2]` |
| `type` | Get type of value | `[1, 2]` | `"array"` |

## Examples

### Example 1: Extract User IDs from Array

**Request:**
```bash
nodi> users | .[*].userId
```

**Response Data:**
```json
[
  {"userId": 1, "id": 1, "title": "Post 1"},
  {"userId": 1, "id": 2, "title": "Post 2"},
  {"userId": 2, "id": 3, "title": "Post 3"}
]
```

**Filtered Output:**
```json
[1, 1, 2]
```

### Example 2: Extract Nested Fields

**Request:**
```bash
nodi> users | .[*].user.name
```

**Response Data:**
```json
[
  {"userId": 1, "user": {"name": "John", "email": "john@example.com"}},
  {"userId": 2, "user": {"name": "Jane", "email": "jane@example.com"}}
]
```

**Filtered Output:**
```json
["John", "Jane"]
```

### Example 3: Get Single Element Field

**Request:**
```bash
nodi> users | .[0].title
```

**Response Data:**
```json
[
  {"id": 1, "title": "First Post"},
  {"id": 2, "title": "Second Post"}
]
```

**Filtered Output:**
```json
"First Post"
```

### Example 4: Count Array Elements

**Request:**
```bash
nodi> users | length
```

**Response Data:**
```json
[{"id": 1}, {"id": 2}, {"id": 3}]
```

**Filtered Output:**
```json
3
```

### Example 5: Extract All Titles

**Request:**
```bash
nodi> posts | .[].title
```

**Response Data:**
```json
[
  {"id": 1, "title": "Post 1", "body": "..."},
  {"id": 2, "title": "Post 2", "body": "..."},
  {"id": 3, "title": "Post 3", "body": "..."}
]
```

**Filtered Output:**
```json
["Post 1", "Post 2", "Post 3"]
```

### Example 6: Nested Object Access

**Request:**
```bash
nodi> profile | .user.email
```

**Response Data:**
```json
{
  "userId": 1,
  "user": {
    "name": "John Doe",
    "email": "john@example.com",
    "address": {
      "city": "New York"
    }
  }
}
```

**Filtered Output:**
```json
"john@example.com"
```

### Example 7: Deep Nesting

**Request:**
```bash
nodi> profile | .user.address.city
```

**Filtered Output:**
```json
"New York"
```

## Real-World Use Cases

### Use Case 1: Quick Validation

Check if API returns expected number of items:

```bash
nodi> get orders -H Cookie:$user1_cookie | length
# Output: 5

nodi> get orders -H Cookie:$user2_cookie | length
# Output: 2
```

### Use Case 2: Extract IDs for Further Requests

Get list of order IDs:

```bash
nodi> get orders | .[*].orderId
# Output: ["ord_123", "ord_456", "ord_789"]
```

### Use Case 3: Verify User Context

Confirm which user the API sees:

```bash
nodi> get profile -H Cookie:$user1_cookie | .userId
# Output: 1

nodi> get profile -H Cookie:$user2_cookie | .userId
# Output: 2
```

### Use Case 4: Extract Email List

Get all user emails:

```bash
nodi> get /api/users | .[].email
# Output: ["john@example.com", "jane@example.com", "bob@example.com"]
```

### Use Case 5: Check Response Structure

```bash
nodi> get profile | keys
# Output: ["userId", "name", "email", "createdAt"]

nodi> get profile | type
# Output: "object"
```

## Combining with Other Features

### Filter + Variable Headers

```bash
# Get user1's order IDs
nodi> get orders -H Cookie:$user1_cookie | .[*].orderId

# Get user2's order IDs
nodi> get orders -H Cookie:$user2_cookie | .[*].orderId
```

### Filter + Multiple Requests

```bash
# Count orders for different users
nodi> get orders -H Cookie:$user1_cookie | length
# Output: 5

nodi> get orders -H Cookie:$user2_cookie | length
# Output: 2

nodi> get orders -H Cookie:$admin_cookie | length
# Output: 15
```

### Chaining Information Extraction

```bash
# Get first user's email
nodi> get /api/users | .[0].email
# Output: "john@example.com"

# Get all user names
nodi> get /api/users | .[].name
# Output: ["John", "Jane", "Bob"]

# Get deeply nested data
nodi> get /api/users | .[*].profile.address.city
# Output: ["New York", "Los Angeles", "Chicago"]
```

## Advanced Filters (with pyjq)

For more complex filtering, install `pyjq`:

```bash
pip install pyjq
```

With pyjq installed, you can use advanced jq syntax:

```bash
# Select with conditions
nodi> users | .[] | select(.userId == 1)

# Map and transform
nodi> users | map(.title)

# Complex selections
nodi> orders | .[] | select(.total > 100) | .orderId
```

## Filter Syntax Quick Reference

```bash
# Basic
.                    # Identity
.field               # Get field
.field.nested        # Nested field

# Arrays
.[]                  # Expand array
.[0]                 # First element
.[0].field           # Field from first element

# Array mapping
.[*].field           # Map field from all elements
.[].field            # Same as .[*].field
.[*].nested.field    # Map nested field

# Utilities
length               # Get length
keys                 # Get object keys
values               # Get object values
type                 # Get type

# With requests
get users | .[*].id              # Get all IDs
get users | .[0].name            # Get first name
get users | length               # Count users
get profile | .user.email        # Get nested email
```

## Troubleshooting

### Issue: Filter returns nothing

**Cause:** Field doesn't exist in data

**Solution:** Check the actual response structure first:
```bash
nodi> get users
# Then apply filter based on actual structure
```

### Issue: "Filter not supported in simple mode"

**Cause:** Complex filter requires pyjq

**Solution:** Install pyjq:
```bash
pip install pyjq
```

### Issue: Array expansion doesn't work

**Cause:** Data is not an array

**Solution:** Check data type:
```bash
nodi> get endpoint | type
# If it's "object", use .field first to get to the array
```

## Tips

✅ **Start simple** - Use `.` first to see the full response structure

✅ **Use length for validation** - Quick way to verify expected results

✅ **Extract IDs for debugging** - `.[*].id` is often useful for verification

✅ **Combine with variables** - Use filters with `-H` flags to test different users

✅ **Chain requests** - Use filter output to understand what to request next

## Summary

Filters make API testing faster by:
- Extracting specific fields without external tools
- Validating response structure quickly
- Comparing data across different users/contexts
- Debugging API responses interactively

All filter operations work seamlessly with variable-based header injection!
