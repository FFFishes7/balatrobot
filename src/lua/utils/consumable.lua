---Consumable target requirements (shared by pack endpoint and gamestate extraction)

local M = {}

--- Get target requirements for a consumable card from G.P_CENTERS configuration
--- @param card_key string Card key (e.g., "c_magician")
--- @return table|nil { min = number, max = number } or { requires_joker = boolean } or nil
function M.get_consumable_target_requirements(card_key)
  if card_key == "c_aura" then
    return { min = 1, max = 1 }
  end

  if card_key == "c_ankh" then
    return { requires_joker = true }
  end

  if not G or not G.P_CENTERS then
    return nil
  end

  local center = G.P_CENTERS[card_key]
  if not center or not center.config then
    return nil
  end

  local config = center.config
  if config.max_highlighted then
    return {
      min = config.min_highlighted or 1,
      max = config.max_highlighted,
    }
  end

  return nil
end

return M
