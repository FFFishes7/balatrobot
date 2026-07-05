-- src/lua/endpoints/tests/sticker_blacklist.lua

-- ==========================================================================
-- Test Stake Sticker Blacklist Endpoint Params
-- ==========================================================================

---@class Request.Endpoint.Test.StickerBlacklist.Params

-- ==========================================================================
-- Test Stake Sticker Blacklist Endpoint
-- ==========================================================================

---@type Endpoint
return {

  name = "test_sticker_blacklist",

  description = "Return localized stake win sticker lines filtered from value.effect",

  schema = {},

  requires_state = nil,

  ---@param _ Request.Endpoint.Test.StickerBlacklist.Params
  ---@param send_response fun(response: Response.Endpoint)
  execute = function(_, send_response)
    local data = BB_GAMESTATE.get_stake_sticker_blacklist()
    send_response({
      success = true,
      lines = data.lines,
      count = data.count,
    })
  end,
}
