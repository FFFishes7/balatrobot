-- src/lua/endpoints/sort.lua

-- ==========================================================================
-- Sort Endpoint Params
-- ==========================================================================

---@class Request.Endpoint.Sort.Params
---@field mode string? sort mode: rank, rank-desc, rank-asc, suit, suit-desc, suit-asc

-- ==========================================================================
-- Sort Endpoint
-- ==========================================================================

---@type Endpoint
return {

  name = "sort",

  description = "Sort hand cards using Balatro's native hand sort logic",

  schema = {
    mode = {
      type = "string",
      required = false,
      description = "Sort mode: rank/rank-desc/value, rank-asc, suit/suit-desc, or suit-asc",
    },
  },

  requires_state = { G.STATES.SELECTING_HAND, G.STATES.SMODS_BOOSTER_OPENED },

  ---@param args Request.Endpoint.Sort.Params
  ---@param send_response fun(response: Response.Endpoint)
  execute = function(args, send_response)
    sendDebugMessage("Init sort()", "BB.ENDPOINTS")

    if not G.hand or not G.hand.cards or #G.hand.cards == 0 then
      send_response({
        message = "No hand available to sort",
        name = BB_ERROR_NAMES.NOT_ALLOWED,
      })
      return
    end

    -- In SMODS_BOOSTER_OPENED, hand is only available in Arcana/Spectral packs.
    if G.STATE == G.STATES.SMODS_BOOSTER_OPENED and #G.hand.cards == 0 then
      send_response({
        message = "No cards to sort. You can only sort hand in Arcana and Spectral packs.",
        name = BB_ERROR_NAMES.NOT_ALLOWED,
      })
      return
    end

    local mode = args.mode or "rank"
    local method = nil

    if mode == "rank" or mode == "rank-desc" or mode == "value" or mode == "value-desc" then
      method = "desc"
    elseif mode == "rank-asc" or mode == "value-asc" then
      method = "asc"
    elseif mode == "suit" or mode == "suit-desc" then
      method = "suit desc"
    elseif mode == "suit-asc" then
      method = "suit asc"
    else
      send_response({
        message = "Sort mode must be one of: rank, rank-desc, rank-asc, suit, suit-desc, suit-asc",
        name = BB_ERROR_NAMES.BAD_REQUEST,
      })
      return
    end

    sendDebugMessage(string.format("Sorting hand with native method '%s'", method), "BB.ENDPOINTS")

    -- These are the same CardArea:sort methods used by Balatro's built-in
    -- "Rank" and "Suit" hand sort buttons.
    G.hand:sort(method)

    G.E_MANAGER:add_event(Event({
      trigger = "condition",
      blocking = false,
      func = function()
        local done = (G.STATE == G.STATES.SELECTING_HAND or G.STATE == G.STATES.SMODS_BOOSTER_OPENED) and G.hand ~= nil
        if done then
          sendDebugMessage("Return sort()", "BB.ENDPOINTS")
          send_response(BB_GAMESTATE.get_gamestate())
        end
        return done
      end,
    }))
  end,
}
