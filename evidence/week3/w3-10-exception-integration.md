# W3-10 exception validation evidence

Date: 12 November 2026

- Portfolio validation is controlled by `portfolio_validation_enabled` and defaults off for standalone compatibility.
- Validation runs before exception ID allocation and persistence.
- Active portfolios continue to creation.
- Missing portfolios return `422 INVALID_PORTFOLIO`.
- Inactive portfolios return `422 PORTFOLIO_INACTIVE`.
- Dependency failures return `503 DEPENDENCY_UNAVAILABLE`.
- Service and API tests prove rejected validation leaves the repository empty and does not consume an in-memory public ID.
- The Exception authored/generated contract retains 8 operations with 0 differences after documenting the approved 503 response.
