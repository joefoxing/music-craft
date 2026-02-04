"""
Optional parameter validation and normalization module.
Handles validation, rounding, and cleaning of optional generation parameters.
"""
from typing import Dict, Any, Optional, Tuple
import decimal


class OptionalParamsValidator:
    """
    Validator for optional generation parameters.
    
    Handles validation, rounding, and cleaning of:
    - styleWeight (0-1, max 2 decimals)
    - weirdnessConstraint (0-1, max 2 decimals)
    - audioWeight (0-1, max 2 decimals)
    - personaId (string, only allowed when customMode=True)
    """
    
    @staticmethod
    def validate_and_normalize(
        style_weight: Optional[float] = None,
        weirdness_constraint: Optional[float] = None,
        audio_weight: Optional[float] = None,
        persona_id: Optional[str] = None,
        custom_mode: bool = False
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Validate and normalize optional parameters.
        
        Args:
            style_weight: Strength of adherence to style (0-1)
            weirdness_constraint: Controls creative deviation (0-1)
            audio_weight: Balance weight for audio features (0-1)
            persona_id: Persona ID to apply
            custom_mode: Whether custom mode is enabled
            
        Returns:
            Tuple of (cleaned_params_dict, error_message)
            cleaned_params_dict contains only valid, normalized parameters
            error_message is None if validation passes, otherwise contains error
        """
        cleaned_params = {}
        errors = []
        
        # Validate and normalize styleWeight
        if style_weight is not None:
            is_valid, normalized_value, error = OptionalParamsValidator._validate_numeric_param(
                "styleWeight", style_weight, 0, 1
            )
            if not is_valid:
                errors.append(error)
            else:
                cleaned_params["styleWeight"] = normalized_value
        
        # Validate and normalize weirdnessConstraint
        if weirdness_constraint is not None:
            is_valid, normalized_value, error = OptionalParamsValidator._validate_numeric_param(
                "weirdnessConstraint", weirdness_constraint, 0, 1
            )
            if not is_valid:
                errors.append(error)
            else:
                cleaned_params["weirdnessConstraint"] = normalized_value
        
        # Validate and normalize audioWeight
        if audio_weight is not None:
            is_valid, normalized_value, error = OptionalParamsValidator._validate_numeric_param(
                "audioWeight", audio_weight, 0, 1
            )
            if not is_valid:
                errors.append(error)
            else:
                cleaned_params["audioWeight"] = normalized_value
        
        # Validate personaId
        if persona_id is not None:
            is_valid, error = OptionalParamsValidator._validate_persona_id(
                persona_id, custom_mode
            )
            if not is_valid:
                errors.append(error)
            else:
                cleaned_params["personaId"] = persona_id
        
        # Return results
        if errors:
            return {}, "; ".join(errors)
        
        return cleaned_params, None
    
    @staticmethod
    def _validate_numeric_param(
        param_name: str,
        value: Any,
        min_val: float,
        max_val: float
    ) -> Tuple[bool, Optional[float], Optional[str]]:
        """
        Validate a numeric parameter and round to 2 decimal places.
        
        Args:
            param_name: Name of the parameter for error messages
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            Tuple of (is_valid, normalized_value, error_message)
        """
        # Check if value is numeric
        try:
            if isinstance(value, str):
                # Try to convert string to float
                numeric_value = float(value)
            else:
                numeric_value = float(value)
        except (ValueError, TypeError):
            return False, None, f"{param_name} must be a number"
        
        # Check range
        if not (min_val <= numeric_value <= max_val):
            return False, None, f"{param_name} must be between {min_val} and {max_val}"
        
        # Round to 2 decimal places
        # Use Decimal for precise rounding to avoid floating point issues
        try:
            # Round using Decimal for precision
            decimal_value = decimal.Decimal(str(numeric_value))
            rounded_value = round(decimal_value, 2)
            normalized_value = float(rounded_value)
        except (decimal.InvalidOperation, ValueError):
            # Fallback to standard rounding
            normalized_value = round(numeric_value, 2)
        
        # Ensure the rounded value is still within bounds
        normalized_value = max(min_val, min(max_val, normalized_value))
        
        return True, normalized_value, None
    
    @staticmethod
    def _validate_persona_id(
        persona_id: Any,
        custom_mode: bool
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate personaId parameter.
        
        Args:
            persona_id: Persona ID to validate
            custom_mode: Whether custom mode is enabled
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if persona_id is a string
        if not isinstance(persona_id, str):
            return False, "personaId must be a string"
        
        # Check if persona_id is non-empty
        if not persona_id.strip():
            return False, "personaId cannot be empty"
        
        # Check if custom_mode is True when persona_id is provided
        if not custom_mode:
            return False, "personaId is only allowed when customMode is true"
        
        return True, None
    
    @staticmethod
    def clean_optional_params(
        params_dict: Dict[str, Any],
        custom_mode: bool = False
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Clean and validate optional parameters from a dictionary.
        
        Args:
            params_dict: Dictionary containing optional parameters
            custom_mode: Whether custom mode is enabled
            
        Returns:
            Tuple of (cleaned_params_dict, error_message)
        """
        # Extract optional parameters
        style_weight = params_dict.get("styleWeight")
        weirdness_constraint = params_dict.get("weirdnessConstraint")
        audio_weight = params_dict.get("audioWeight")
        persona_id = params_dict.get("personaId")
        
        # Convert snake_case to camelCase if needed
        if style_weight is None:
            style_weight = params_dict.get("style_weight")
        if weirdness_constraint is None:
            weirdness_constraint = params_dict.get("weirdness_constraint")
        if audio_weight is None:
            audio_weight = params_dict.get("audio_weight")
        if persona_id is None:
            persona_id = params_dict.get("persona_id")
        
        # Validate and normalize
        return OptionalParamsValidator.validate_and_normalize(
            style_weight=style_weight,
            weirdness_constraint=weirdness_constraint,
            audio_weight=audio_weight,
            persona_id=persona_id,
            custom_mode=custom_mode
        )


# Convenience function for easy import
def validate_optional_params(params_dict: Dict[str, Any], custom_mode: bool = False) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Convenience function to validate optional parameters.
    
    Args:
        params_dict: Dictionary containing optional parameters
        custom_mode: Whether custom mode is enabled
        
    Returns:
        Tuple of (cleaned_params_dict, error_message)
    """
    return OptionalParamsValidator.clean_optional_params(params_dict, custom_mode)