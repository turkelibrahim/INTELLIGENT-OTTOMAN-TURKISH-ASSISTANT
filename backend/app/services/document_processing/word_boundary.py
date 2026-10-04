"""Word boundary reconstruction heuristics for Ottoman/Arabic script."""

from __future__ import annotations

import statistics
from typing import Sequence
import math

from .ocr_engine import BoxItem

def get_arabic_joining_type(char: str) -> str:
    """
    Returns the joining type of an Arabic/Ottoman character.
    D = Dual joining (joins both sides, e.g. B, T, TH, J, H, KH, S, SH...)
    R = Right joining only (e.g. A, D, DH, R, Z, W)
    U = Non-joining (e.g. Hamza)
    C = Transparent/Combining mark (e.g. Fatha, Kasra, Damma)
    N = Non-Arabic / Punctuation / Digits
    """
    code = ord(char)
    # Basic Ottoman/Arabic Right-joining letters
    right_joining = {
        0x0627, # Alef
        0x0622, # Alef with madda
        0x0623, # Alef with hamza above
        0x0625, # Alef with hamza below
        0x062F, # Dal
        0x0630, # Thal
        0x0631, # Reh
        0x0632, # Zain
        0x0698, # Jeh (Persian/Ottoman)
        0x0648, # Waw
        0x0624, # Waw with hamza
        0x06C6, # Waw with oe
        0x06C7, # Waw with u
        0x06C8, # Waw with yu
        0x06CB, # Waw with vee
    }
    
    # Combining marks
    if 0x0610 <= code <= 0x061A or 0x064B <= code <= 0x065F or 0x0670 <= code <= 0x06D3:
        return 'C'
        
    if char.isdigit():
        return 'N'
        
    if char.isspace() or char in ".,!?;:'\"()[]{}؟،؛-":
        return 'N'
        
    if 0x0600 <= code <= 0x06FF or 0x0750 <= code <= 0x077F or 0x08A0 <= code <= 0x08FF:
        if code in right_joining:
            return 'R'
        if code == 0x0621: # Hamza
            return 'U'
        return 'D' # Default to Dual joining for other Arabic letters
        
    return 'N'

def get_last_base_char(text: str) -> str:
    """Returns the last non-combining character of a string (logical end, visual left)."""
    for char in reversed(text):
        if get_arabic_joining_type(char) != 'C':
            return char
    return text[-1] if text else ""

def get_first_base_char(text: str) -> str:
    """Returns the first non-combining character of a string (logical start, visual right)."""
    for char in text:
        if get_arabic_joining_type(char) != 'C':
            return char
    return text[0] if text else ""

def can_visually_join(right_text: str, left_text: str) -> bool:
    """
    In RTL, right_text is logically BEFORE left_text.
    Visual joining happens if the last char of right_text joins to the left (is D),
    and the first char of left_text joins to the right (is D or R).
    """
    if not right_text or not left_text:
        return False
        
    last_right = get_last_base_char(right_text)
    first_left = get_first_base_char(left_text)
    
    right_type = get_arabic_joining_type(last_right)
    left_type = get_arabic_joining_type(first_left)
    
    # Right component's left side must be able to join (must be D, as R only joins right)
    # Left component's right side must be able to join (can be D or R)
    return right_type == 'D' and left_type in ('D', 'R')

def extract_boundary_features(right_comp: BoxItem, left_comp: BoxItem, median_height: float) -> dict:
    """
    Extracts features between two RTL components.
    right_comp is logically earlier (visually on the right).
    left_comp is logically later (visually on the left).
    """
    # Horizontal gap (Right component's left edge to Left component's right edge)
    gap = right_comp.bbox[0] - left_comp.bbox[2]
    
    # Normalize gap by median line height
    normalized_gap = gap / median_height if median_height > 0 else 0
    
    # Check if text implies a visual join
    joining_compatible = can_visually_join(right_comp.text.strip(), left_comp.text.strip())
    
    # Punctuation/Digit checks
    last_right = right_comp.text.strip()[-1:] if right_comp.text.strip() else ""
    first_left = left_comp.text.strip()[:1] if left_comp.text.strip() else ""
    
    is_punctuation = last_right in ".,!?;:'\"()[]{}؟،؛-" or first_left in ".,!?;:'\"()[]{}؟،؛-"
    is_digit = last_right.isdigit() or first_left.isdigit()
    
    return {
        "gap": gap,
        "normalized_gap": normalized_gap,
        "joining_compatible": joining_compatible,
        "is_punctuation": is_punctuation,
        "is_digit": is_digit,
        "right_conf": right_comp.confidence,
        "left_conf": left_comp.confidence
    }

def score_word_boundary(features: dict, config: dict) -> float:
    """
    Returns a score representing the probability that there should be a SPACE
    between the two components. Higher score = more likely to insert a space.
    """
    score = 0.0
    
    # Base gap factor
    score += features["normalized_gap"] * float(config.get("gap_weight", 1.0))
    
    # Joining penalty (if they can visually join, it's less likely to be a space,
    # unless the gap is huge)
    if features["joining_compatible"]:
        score -= float(config.get("joining_penalty", 0.5))
        
    # Punctuation / Digits usually imply boundaries if not part of a larger number
    if features["is_punctuation"]:
        score += float(config.get("punctuation_bonus", 0.3))
        
    if features["is_digit"]:
        # Spaces around digits are very common in ground truth
        score += float(config.get("digit_bonus", 0.2))
        
    return score

def split_internal_components(text: str, config: dict) -> str:
    """
    Splits long strings at non-left-joining characters to simulate missing spaces.
    Right-joining only chars: Alef, Dal, Thal, Reh, Zain, Waw, Jeh.
    """
    if not text: return text
    
    parts = text.split(" ")
    out_parts = []
    
    max_len = int(config.get("internal_split_min_length", 8))
    
    for part in parts:
        if len(part) < max_len:
            out_parts.append(part)
            continue
            
        # Try to split the long word at the best Right-joining character
        # We want to split such that the resulting words are roughly balanced
        best_split_idx = -1
        best_balance = float('inf')
        
        for i, char in enumerate(part):
            if i == 0 or i == len(part) - 1:
                continue # don't split at very beginning or end
                
            # If it's a right-joining (R) or un-joining (U) char, it doesn't join to the left.
            # In RTL, 'left' is the next character in the string.
            if get_arabic_joining_type(char) in ('R', 'U'):
                # Check next char to ensure we aren't splitting before a combining mark
                if i + 1 < len(part) and get_arabic_joining_type(part[i+1]) == 'C':
                    continue
                    
                left_len = i + 1
                right_len = len(part) - left_len
                
                # We prefer splits that leave chunks of at least 3 chars
                if left_len >= 3 and right_len >= 3:
                    balance = abs(left_len - right_len)
                    if balance < best_balance:
                        best_balance = balance
                        best_split_idx = i
                        
        if best_split_idx != -1:
            out_parts.append(part[:best_split_idx+1])
            out_parts.append(part[best_split_idx+1:])
        else:
            out_parts.append(part)
            
    return " ".join(out_parts)

def reconstruct_rtl_line_text_v2(components: Sequence[BoxItem], config: dict) -> str:
    """
    Advanced word-boundary reconstruction.
    """
    usable = [item for item in components if item.text and item.confidence >= float(config.get("low_confidence_threshold", 0.0))]
    if not usable:
        return ""
        
    heights = [max(1.0, item.bbox[3] - item.bbox[1]) for item in usable]
    median_height = statistics.median(heights) if heights else 1.0
    
    # Sort RTL: Visually right-most first
    ordered = sorted(usable, key=lambda item: (-item.bbox[2], -item.bbox[0], item.id))
    
    parts: list[str] = []
    previous: BoxItem | None = None
    
    threshold = float(config.get("boundary_score_threshold", 0.25))
    enable_internal_split = config.get("enable_internal_split", False)
    
    for item in ordered:
        text = item.text.strip()
        if not text:
            continue
            
        if enable_internal_split:
            text = split_internal_components(text, config)
            
        if previous is None:
            parts.append(text)
        else:
            features = extract_boundary_features(previous, item, median_height)
            
            # Simple fallback to Q6 if enabled
            if config.get("strategy") == "Q6_baseline":
                gap = max(0.0, previous.bbox[0] - item.bbox[2])
                attach = gap / median_height <= float(config.get("join_gap_ratio", 0.18)) or previous.text.strip()[-1:] in ".,;:!?،؛؟)"
                if attach and parts:
                    parts[-1] = parts[-1] + " " + text if text.startswith(" ") else parts[-1] + text
                else:
                    parts.append(text)
            else:
                score = score_word_boundary(features, config)
                insert_space = score >= threshold
                
                if insert_space:
                    parts.append(text)
                else:
                    # Attach to previous
                    parts[-1] = parts[-1] + " " + text if text.startswith(" ") else parts[-1] + text
                    
        previous = item
        
    return " ".join(part for part in parts if part).strip()
