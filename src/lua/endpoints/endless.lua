-- src/lua/endpoints/endless.lua

-- ==========================================================================
-- Endless Endpoint Params
-- ==========================================================================

---@class Request.Endpoint.Endless.Params

-- ==========================================================================
-- Endless Endpoint
-- ==========================================================================

---@type Endpoint
return {

  name = "endless",

  description = "Dismiss victory overlay to continue in endless mode",

  schema = {},

  requires_state = { G.STATES.ROUND_EVAL },

  ---@param _ Request.Endpoint.Endless.Params
  ---@param send_response fun(response: Response.Endpoint)
  execute = function(_, send_response)
    sendDebugMessage("Init endless()", "BB.ENDPOINTS")

    if not G.GAME or not G.GAME.won then
      send_response({
        message = "Run has not been won yet",
        name = BB_ERROR_NAMES.NOT_ALLOWED,
      })
      return
    end

    if not BB_GAMESTATE.has_victory_overlay() then
      send_response({
        message = "Victory overlay is not showing",
        name = BB_ERROR_NAMES.NOT_ALLOWED,
      })
      return
    end

    G.FUNCS.exit_overlay_menu()

    G.E_MANAGER:add_event(Event({
      trigger = "condition",
      blocking = false,
      created_on_pause = true,
      func = function()
        if G.OVERLAY_MENU ~= nil then
          return false
        end

        if G.STATE ~= G.STATES.ROUND_EVAL or not G.STATE_COMPLETE then
          return false
        end

        if not G.round_eval then
          return false
        end

        local has_cash_out = false
        for _, b in ipairs(G.I.UIBOX) do
          if b:get_UIE_by_ID("cash_out_button") then
            has_cash_out = true
            break
          end
        end

        if not has_cash_out then
          return false
        end

        sendDebugMessage("Return endless()", "BB.ENDPOINTS")
        send_response(BB_GAMESTATE.get_gamestate())
        return true
      end,
    }))
  end,
}
