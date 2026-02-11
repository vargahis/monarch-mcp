# Vendored MonarchMoney Library

This directory contains a vendored copy of the MonarchMoney library from:
https://github.com/bradleyseanf/monarchmoneycommunity

## Why Vendored?

The original `hammem/monarchmoney` library hardcodes `trusted_device: False` in authentication requests, which causes Monarch Money's API to return **short-lived tokens (1 hour expiration)** instead of long-lived tokens (months).

This fork by bradleyseanf:
- Sets `trusted_device: True` by default
- Validates that tokens are long-lived (not JWTs)
- Rejects short-lived tokens with clear error messages
- Includes the updated API domain (api.monarch.com)

## Key Changes

1. **trusted_device: True** - Requests long-lived browser-style sessions
2. **Token Validation** - Ensures `tokenExpiration == null` for long-lived tokens
3. **JWT Detection** - Rejects 1-hour tokens (identified by two dots in token string)

## Version

Based on: monarchmoneycommunity v1.3.0 (bradleyseanf fork)

## License

MIT License - Same as original library
