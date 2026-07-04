-- src/lua/endpoints/debuff.lua

-- ==========================================================================
-- Debuff Endpoint Params
-- ==========================================================================

---@class Request.Endpoint.Debuff.Params
---@field cards integer[] 0-based indices of hand cards to debuff or clear
---@field debuff boolean true to debuff, false to clear debuff

-- ==========================================================================
-- Debuff Endpoint (debug / estimate testing)
-- ==========================================================================

---@type Endpoint
return {

  name = "debuff",

  description = "Set debuff state on hand cards (debug / estimate testing)",

  schema = {
    cards = {
      type = "array",
      required = true,
      items = "integer",
      description = "0-based indices of hand cards",
    },
    debuff = {
      type = "boolean",
      required = true,
      description = "true to debuff cards, false to clear debuff",
    },
  },

  requires_state = { G.STATES.SELECTING_HAND },

  ---@param args Request.Endpoint.Debuff.Params
  ---@param send_response fun(response: Response.Endpoint)
  execute = function(args, send_response)
    sendDebugMessage("Init debuff()", "BB.ENDPOINTS")

    if #args.cards == 0 then
      send_response({
        message = "Must provide at least one card index",
        name = BB_ERROR_NAMES.BAD_REQUEST,
      })
      return
    end

    for _, card_index in ipairs(args.cards) do
      if type(card_index) ~= "number" or card_index < 0 then
        send_response({
          message = "Invalid card index: " .. tostring(card_index),
          name = BB_ERROR_NAMES.BAD_REQUEST,
        })
        return
      end
      local card = G.hand.cards[card_index + 1]
      if not card then
        send_response({
          message = "Invalid card index: " .. card_index,
          name = BB_ERROR_NAMES.BAD_REQUEST,
        })
        return
      end
      card:set_debuff(args.debuff)
    end

    sendDebugMessage("Return debuff()", "BB.ENDPOINTS")
    send_response(BB_GAMESTATE.get_gamestate())
  end,
}
