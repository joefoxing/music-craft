"""
API routes for the Music Cover Generator application.
Contains API endpoints for music generation, status checking, and downloads.
"""
from flask import Blueprint, request, jsonify, current_app, Response
import requests

from app import limiter
from app.config import Config
from app.core.api_client import KieAPIClient
from app.core.utils import ResponseUtils, DateTimeUtils, URLUtils, FileUtils
from app.core.validation import ModelValidator, ParameterValidator
from app.services.usage_limits import check_allowed, is_successful_kie_response, record_usage


api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/templates', methods=['OPTIONS'])
def handle_templates_options():
    """Handle CORS preflight requests for templates endpoint."""
    response = jsonify({'status': 'ok'})
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


@api_bp.route('/generate-music', methods=['POST'])
@limiter.limit("10 per minute")
def generate_music():
    """Generate music from text prompt using Kie API."""
    try:
        data = request.json

        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Required parameters
        prompt = data.get('prompt')
        custom_mode = data.get('custom_mode', False)
        instrumental = data.get('instrumental', False)
        model = data.get('model', 'V5')
        
        if not prompt:
            return jsonify(ResponseUtils.create_error_response('prompt is required')), 400

        allowed, usage_meta, status_code = check_allowed(units=1)
        if not allowed:
            payload = ResponseUtils.create_error_response(usage_meta.get('error', 'Usage limit exceeded'), status_code)
            payload.update(usage_meta)
            return jsonify(payload), status_code
        
        # Optional parameters
        style = data.get('style')
        title = data.get('title')
        call_back_url = data.get('call_back_url')
        
        # If no callback URL provided, construct default from public base URL
        if not call_back_url:
            public_base_url = Config.get_public_base_url(request)
            call_back_url = f"{public_base_url}/callback"
        
        # Optional advanced parameters
        optional_params = {
            'negativeTags': data.get('negative_tags'),
            'vocalGender': data.get('vocal_gender'),
            'styleWeight': data.get('style_weight'),
            'weirdnessConstraint': data.get('weirdness_constraint'),
            'audioWeight': data.get('audio_weight'),
            'personaId': data.get('persona_id')
        }
        
        # Validate optional parameters
        validator = ParameterValidator()
        validated_optional_params, validation_error = validator.validate_optional_parameters(
            optional_params, custom_mode
        )
        
        if validation_error:
            return jsonify(ResponseUtils.create_error_response(validation_error)), 400

        # Initialize API client
        client = KieAPIClient()
        
        # Validate parameters
        is_valid, error_msg = client.validate_parameters(
            custom_mode=custom_mode,
            instrumental=instrumental,
            prompt=prompt,
            style=style,
            title=title,
            model=model
        )
        
        if not is_valid:
            return jsonify(ResponseUtils.create_error_response(error_msg)), 400
        
        # Call Kie API direct music generation endpoint
        response = client.generate_music_direct(
            custom_mode=custom_mode,
            instrumental=instrumental,
            call_back_url=call_back_url,
            model=model,
            prompt=prompt,
            style=style,
            title=title,
            **validated_optional_params
        )

        if is_successful_kie_response(response):
            record_usage('generate_music', units=1)
            response['usage'] = usage_meta
        else:
            _, usage_meta_now, _ = check_allowed(units=0)
            response['usage'] = usage_meta_now
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error generating music: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/generate-music-direct', methods=['POST'])
@limiter.limit("10 per minute")
def generate_music_direct():
    """Generate music directly from text prompt (no upload)."""
    try:
        data = request.json

        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Required parameters
        prompt = data.get('prompt')
        custom_mode = data.get('custom_mode', False)
        instrumental = data.get('instrumental', False)
        model = data.get('model', 'V5')
        
        if not prompt:
            return jsonify(ResponseUtils.create_error_response('prompt is required')), 400

        allowed, usage_meta, status_code = check_allowed(units=1)
        if not allowed:
            payload = ResponseUtils.create_error_response(usage_meta.get('error', 'Usage limit exceeded'), status_code)
            payload.update(usage_meta)
            return jsonify(payload), status_code
        
        # Optional parameters
        style = data.get('style')
        title = data.get('title')
        call_back_url = data.get('call_back_url')
        
        # If no callback URL provided, construct default from public base URL
        if not call_back_url:
            public_base_url = Config.get_public_base_url(request)
            call_back_url = f"{public_base_url}/callback"
        
        # Optional advanced parameters
        optional_params = {
            'negativeTags': data.get('negative_tags'),
            'vocalGender': data.get('vocal_gender'),
            'styleWeight': data.get('style_weight'),
            'weirdnessConstraint': data.get('weirdness_constraint'),
            'audioWeight': data.get('audio_weight'),
            'personaId': data.get('persona_id')
        }
        
        # Validate optional parameters
        validator = ParameterValidator()
        validated_optional_params, validation_error = validator.validate_optional_parameters(
            optional_params, custom_mode
        )
        
        if validation_error:
            return jsonify(ResponseUtils.create_error_response(validation_error)), 400

        # Initialize API client
        client = KieAPIClient()
        
        # Validate parameters
        is_valid, error_msg = client.validate_parameters(
            custom_mode=custom_mode,
            instrumental=instrumental,
            prompt=prompt,
            style=style,
            title=title,
            model=model
        )
        
        if not is_valid:
            return jsonify(ResponseUtils.create_error_response(error_msg)), 400
        
        # Call Kie API direct music generation endpoint
        response = client.generate_music_direct(
            custom_mode=custom_mode,
            instrumental=instrumental,
            call_back_url=call_back_url,
            model=model,
            prompt=prompt,
            style=style,
            title=title,
            **validated_optional_params
        )

        if is_successful_kie_response(response):
            record_usage('generate_music_direct', units=1)
            response['usage'] = usage_meta
        else:
            _, usage_meta_now, _ = check_allowed(units=0)
            response['usage'] = usage_meta_now
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error generating music direct: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/v1/generate', methods=['POST'])
@limiter.limit("10 per minute")
def generate_music_v1():
    """
    Generate music using the /api/v1/generate endpoint.
    
    Core required parameters: customMode, instrumental, callBackUrl, model, prompt
    
    For Custom Mode (customMode: true):
    - If instrumental: true, must provide style and title
    - If instrumental: false, must provide style, prompt (used as exact lyrics), and title
    
    For Non-custom Mode (customMode: false):
    - Only prompt (max 500 characters) is required
    
    Optional parameters for Custom Mode:
    - vocalGender ('m' or 'f'), styleWeight (0-1), weirdnessConstraint (0-1),
      audioWeight (0-1), negativeTags, personaId
    """
    try:
        data = request.json

        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Extract parameters with correct naming (camelCase as per API spec)
        custom_mode = data.get('customMode', False)
        instrumental = data.get('instrumental', False)
        call_back_url = data.get('callBackUrl')
        model = data.get('model', 'V5')
        prompt = data.get('prompt')
        
        # Validate required parameters
        if not call_back_url:
            return jsonify(ResponseUtils.create_error_response('callBackUrl is required')), 400
        if not model:
            return jsonify(ResponseUtils.create_error_response('model is required')), 400
        if not prompt:
            return jsonify(ResponseUtils.create_error_response('prompt is required')), 400

        allowed, usage_meta, status_code = check_allowed(units=1)
        if not allowed:
            payload = ResponseUtils.create_error_response(usage_meta.get('error', 'Usage limit exceeded'), status_code)
            payload.update(usage_meta)
            return jsonify(payload), status_code
        
        # Extract optional parameters
        style = data.get('style')
        title = data.get('title')
        
        # Extract advanced optional parameters
        optional_params = {
            'negativeTags': data.get('negativeTags'),
            'vocalGender': data.get('vocalGender'),
            'styleWeight': data.get('styleWeight'),
            'weirdnessConstraint': data.get('weirdnessConstraint'),
            'audioWeight': data.get('audioWeight'),
            'personaId': data.get('personaId')
        }
        
        # Validate optional parameters
        validator = ParameterValidator()
        validated_optional_params, validation_error = validator.validate_optional_parameters(
            optional_params, custom_mode
        )
        
        if validation_error:
            return jsonify(ResponseUtils.create_error_response(validation_error)), 400
        
        # Initialize API client
        client = KieAPIClient()
        
        # Validate parameters according to specification
        is_valid, error_msg = client.validate_parameters_v1(
            custom_mode=custom_mode,
            instrumental=instrumental,
            prompt=prompt,
            style=style,
            title=title,
            model=model,
            call_back_url=call_back_url
        )
        
        if not is_valid:
            return jsonify(ResponseUtils.create_error_response(error_msg)), 400
        
        # Call the new direct music generation endpoint
        response = client.generate_music_direct(
            custom_mode=custom_mode,
            instrumental=instrumental,
            call_back_url=call_back_url,
            model=model,
            prompt=prompt,
            style=style,
            title=title,
            **validated_optional_params
        )

        if is_successful_kie_response(response):
            record_usage('generate_music_v1', units=1)
            response['usage'] = usage_meta
        else:
            _, usage_meta_now, _ = check_allowed(units=0)
            response['usage'] = usage_meta_now
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error generating music via v1 endpoint: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/generate-lyrics', methods=['POST'])
@limiter.limit("20 per minute")
def generate_lyrics():
    """Generate lyrics from text prompt using Kie API."""
    try:
        data = request.json

        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Required parameters
        prompt = data.get('prompt')
        call_back_url = data.get('call_back_url')
        
        if not prompt:
            return jsonify(ResponseUtils.create_error_response('prompt is required')), 400
        
        # Validate prompt length (max 200 words as per API docs)
        word_count = len(prompt.split())
        if word_count > 200:
            return jsonify(ResponseUtils.create_error_response(
                f'Prompt too long: {word_count} words. Maximum is 200 words.'
            )), 400

        allowed, usage_meta, status_code = check_allowed(units=1)
        if not allowed:
            payload = ResponseUtils.create_error_response(usage_meta.get('error', 'Usage limit exceeded'), status_code)
            payload.update(usage_meta)
            return jsonify(payload), status_code
        
        # Initialize API client
        client = KieAPIClient()
        
        # Call Kie API for lyric generation
        response = client.generate_lyrics(
            prompt=prompt,
            call_back_url=call_back_url
        )

        if is_successful_kie_response(response):
            record_usage('generate_lyrics', units=1)
            response['usage'] = usage_meta
        else:
            _, usage_meta_now, _ = check_allowed(units=0)
            response['usage'] = usage_meta_now
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error generating lyrics: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/v1/lyrics/record-info', methods=['GET'])
def get_lyrics_record_info():
    """Get status and results of a lyrics generation task."""
    try:
        task_id = request.args.get('taskId')
        if not task_id:
            return jsonify(ResponseUtils.create_error_response('taskId query parameter is required')), 400

        current_app.logger.info(f"Getting lyrics record info for task_id: {task_id}")
        client = KieAPIClient()
        result = client.get_lyrics_record_info(task_id)
        current_app.logger.info(f"Lyrics record info response received for {task_id}")
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error getting lyrics record info: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/generate-cover', methods=['POST'])
@limiter.limit("10 per minute")
def generate_cover():
    """Generate music cover using Kie API."""
    try:
        data = request.json

        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Required parameters
        upload_url = data.get('upload_url')
        prompt = data.get('prompt')
        custom_mode = data.get('custom_mode', False)
        instrumental = data.get('instrumental', False)
        model = data.get('model', 'V5')
        
        if not upload_url:
            return jsonify(ResponseUtils.create_error_response('upload_url is required')), 400
        if not prompt:
            return jsonify(ResponseUtils.create_error_response('prompt is required')), 400

        allowed, usage_meta, status_code = check_allowed(units=1)
        if not allowed:
            payload = ResponseUtils.create_error_response(usage_meta.get('error', 'Usage limit exceeded'), status_code)
            payload.update(usage_meta)
            return jsonify(payload), status_code
        
        # Optional parameters
        style = data.get('style')
        title = data.get('title')
        call_back_url = data.get('call_back_url')
        
        # Optional advanced parameters
        optional_params = {
            'negativeTags': data.get('negative_tags'),
            'vocalGender': data.get('vocal_gender'),
            'styleWeight': data.get('style_weight'),
            'weirdnessConstraint': data.get('weirdness_constraint'),
            'audioWeight': data.get('audio_weight'),
            'personaId': data.get('persona_id')
        }
        
        # Validate optional parameters
        validator = ParameterValidator()
        validated_optional_params, validation_error = validator.validate_optional_parameters(
            optional_params, custom_mode
        )
        
        if validation_error:
            return jsonify(ResponseUtils.create_error_response(validation_error)), 400
        
        # Initialize API client
        client = KieAPIClient()
        
        # Validate parameters
        is_valid, error_msg = client.validate_parameters(
            custom_mode=custom_mode,
            instrumental=instrumental,
            prompt=prompt,
            style=style,
            title=title,
            model=model
        )
        
        if not is_valid:
            return jsonify(ResponseUtils.create_error_response(error_msg)), 400
        
        # Call Kie API
        response = client.upload_and_cover_audio(
            upload_url=upload_url,
            prompt=prompt,
            custom_mode=custom_mode,
            instrumental=instrumental,
            model=model,
            call_back_url=call_back_url,
            style=style,
            title=title,
            **validated_optional_params
        )

        if is_successful_kie_response(response):
            record_usage('generate_cover', units=1)
            response['usage'] = usage_meta
        else:
            _, usage_meta_now, _ = check_allowed(units=0)
            response['usage'] = usage_meta_now
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error generating cover: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/generate-extend', methods=['POST'])
@limiter.limit("10 per minute")
def generate_extend():
    """Generate audio extension using Kie API."""
    try:
        data = request.json

        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Required parameters
        upload_url = data.get('upload_url')
        prompt = data.get('prompt')
        continue_at = data.get('continue_at')
        
        # Use simple validation for now since extend might have different rules
        # but basically needs prompt and url
        if not upload_url:
            return jsonify(ResponseUtils.create_error_response('upload_url is required')), 400
        if not prompt:
            return jsonify(ResponseUtils.create_error_response('prompt is required')), 400
        if continue_at is None:
            return jsonify(ResponseUtils.create_error_response('continue_at is required')), 400
            
        try:
            continue_at = int(continue_at)
        except ValueError:
            return jsonify(ResponseUtils.create_error_response('continue_at must be an integer (seconds)')), 400

        allowed, usage_meta, status_code = check_allowed(units=1)
        if not allowed:
            payload = ResponseUtils.create_error_response(usage_meta.get('error', 'Usage limit exceeded'), status_code)
            payload.update(usage_meta)
            return jsonify(payload), status_code
            
        # Other parameters
        instrumental = data.get('instrumental', False)
        model = data.get('model', 'V5')
        style = data.get('style')
        title = data.get('title')
        call_back_url = data.get('call_back_url')
        default_param_flag = data.get('default_param_flag', True)
        
        # Optional advanced parameters
        optional_params = {
            'negativeTags': data.get('negative_tags'),
            'vocalGender': data.get('vocal_gender'),
            'styleWeight': data.get('style_weight'),
            'weirdnessConstraint': data.get('weirdness_constraint'),
            'audioWeight': data.get('audio_weight'),
            'personaId': data.get('persona_id')
        }
        
        # Validate optional parameters
        validator = ParameterValidator()
        validated_optional_params, validation_error = validator.validate_optional_parameters(
            optional_params, custom_mode=False  # extend doesn't use custom_mode, but personaId not allowed
        )
        
        if validation_error:
            return jsonify(ResponseUtils.create_error_response(validation_error)), 400
        
        # Initialize API client
        client = KieAPIClient()
        
        # Call Kie API
        response = client.upload_and_extend_audio(
            upload_url=upload_url,
            continue_at=continue_at,
            prompt=prompt,
            instrumental=instrumental,
            model=model,
            call_back_url=call_back_url,
            style=style,
            title=title,
            default_param_flag=default_param_flag,
            **validated_optional_params
        )

        if is_successful_kie_response(response):
            record_usage('generate_extend', units=1)
            response['usage'] = usage_meta
        else:
            _, usage_meta_now, _ = check_allowed(units=0)
            response['usage'] = usage_meta_now

        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error generating extension: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/generate-music-video', methods=['POST'])
@limiter.limit("5 per minute")
def generate_music_video():
    """Generate music video using Kie API."""
    try:
        data = request.json

        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Required parameters
        task_id = data.get('task_id')
        audio_id = data.get('audio_id')
        
        if not task_id:
            return jsonify(ResponseUtils.create_error_response('task_id is required')), 400
        if not audio_id:
            return jsonify(ResponseUtils.create_error_response('audio_id is required')), 400

        allowed, usage_meta, status_code = check_allowed(units=1)
        if not allowed:
            payload = ResponseUtils.create_error_response(usage_meta.get('error', 'Usage limit exceeded'), status_code)
            payload.update(usage_meta)
            return jsonify(payload), status_code
        
        # Optional parameters
        author = data.get('author')
        domain_name = data.get('domain_name')
        
        # Get callback URL
        public_base_url = Config.get_public_base_url(request)
        call_back_url = f"{public_base_url}/callback"
        
        # Initialize API client
        client = KieAPIClient()
        
        # Call Kie API to generate music video
        response = client.generate_music_video(
            task_id=task_id,
            audio_id=audio_id,
            call_back_url=call_back_url,
            author=author,
            domain_name=domain_name
        )

        if is_successful_kie_response(response):
            record_usage('generate_music_video', units=1)
            response['usage'] = usage_meta
        else:
            _, usage_meta_now, _ = check_allowed(units=0)
            response['usage'] = usage_meta_now
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error generating music video: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/add-instrumental', methods=['POST'])
@limiter.limit("10 per minute")
def add_instrumental():
    """Add instrumental using Kie API."""
    try:
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Accept both camelCase and snake_case parameters
        # Required parameters
        upload_url = data.get('uploadUrl') or data.get('upload_url')
        title = data.get('title')
        
        if not upload_url:
            return jsonify(ResponseUtils.create_error_response('uploadUrl is required')), 400
        if not title:
            return jsonify(ResponseUtils.create_error_response('title is required')), 400

        allowed, usage_meta, status_code = check_allowed(units=1)
        if not allowed:
            payload = ResponseUtils.create_error_response(usage_meta.get('error', 'Usage limit exceeded'), status_code)
            payload.update(usage_meta)
            return jsonify(payload), status_code
        
        # Optional parameters - accept both naming conventions
        negative_tags = data.get('negativeTags') or data.get('negative_tags')
        tags = data.get('tags')
        call_back_url = data.get('callBackUrl') or data.get('call_back_url')
        model = data.get('model', 'V4_5PLUS')
        vocal_gender = data.get('vocalGender') or data.get('vocal_gender', 'm')
        
        # Handle numeric parameters with both naming conventions
        style_weight = data.get('styleWeight') or data.get('style_weight', 0.61)
        weirdness_constraint = data.get('weirdnessConstraint') or data.get('weirdness_constraint', 0.72)
        audio_weight = data.get('audioWeight') or data.get('audio_weight', 0.65)
        
        # Convert to float if they're strings
        try:
            style_weight = float(style_weight)
        except (ValueError, TypeError):
            style_weight = 0.61
            
        try:
            weirdness_constraint = float(weirdness_constraint)
        except (ValueError, TypeError):
            weirdness_constraint = 0.72
            
        try:
            audio_weight = float(audio_weight)
        except (ValueError, TypeError):
            audio_weight = 0.65
        
        # Validate numeric parameters
        validator = ParameterValidator()
        
        # Create optional params dict for validation
        optional_params = {
            'styleWeight': style_weight,
            'weirdnessConstraint': weirdness_constraint,
            'audioWeight': audio_weight
        }
        
        # Validate optional parameters (add-instrumental doesn't use custom_mode or personaId)
        validated_optional_params, validation_error = validator.validate_optional_parameters(
            optional_params, custom_mode=False
        )
        
        if validation_error:
            return jsonify(ResponseUtils.create_error_response(validation_error)), 400
        
        # Extract validated values
        style_weight = validated_optional_params.get('styleWeight', 0.61)
        weirdness_constraint = validated_optional_params.get('weirdnessConstraint', 0.72)
        audio_weight = validated_optional_params.get('audioWeight', 0.65)
        
        # If no callback URL provided, construct default from public base URL
        if not call_back_url:
            public_base_url = Config.get_public_base_url(request)
            call_back_url = f"{public_base_url}/callback"
        
        # Initialize API client
        client = KieAPIClient()
        
        # Call Kie API to add instrumental
        response = client.add_instrumental(
            upload_url=upload_url,
            title=title,
            negative_tags=negative_tags,
            tags=tags,
            call_back_url=call_back_url,
            model=model,
            vocal_gender=vocal_gender,
            style_weight=style_weight,
            weirdness_constraint=weirdness_constraint,
            audio_weight=audio_weight
        )
        
        if is_successful_kie_response(response):
            record_usage('add_instrumental', units=1)
            response['usage'] = usage_meta
        else:
            _, usage_meta_now, _ = check_allowed(units=0)
            response['usage'] = usage_meta_now
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error adding instrumental: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/add-vocals', methods=['POST'])
@limiter.limit("10 per minute")
def add_vocals():
    """Add AI-generated vocals to an existing instrumental using Kie API."""
    try:
        data = request.json

        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Accept both camelCase and snake_case parameters
        # Required parameters
        upload_url = data.get('uploadUrl') or data.get('upload_url')
        prompt = data.get('prompt')
        title = data.get('title')
        
        if not upload_url:
            return jsonify(ResponseUtils.create_error_response('uploadUrl is required')), 400
        if not prompt:
            return jsonify(ResponseUtils.create_error_response('prompt is required')), 400
        if not title:
            return jsonify(ResponseUtils.create_error_response('title is required')), 400

        allowed, usage_meta, status_code = check_allowed(units=1)
        if not allowed:
            payload = ResponseUtils.create_error_response(usage_meta.get('error', 'Usage limit exceeded'), status_code)
            payload.update(usage_meta)
            return jsonify(payload), status_code
        
        # Optional parameters - accept both naming conventions
        style = data.get('style')
        tags = data.get('tags')
        negative_tags = data.get('negativeTags') or data.get('negative_tags')
        call_back_url = data.get('callBackUrl') or data.get('call_back_url')
        model = data.get('model', 'V5')
        vocal_gender = data.get('vocalGender') or data.get('vocal_gender', 'male')
        
        # Handle numeric parameters with both naming conventions
        style_weight = data.get('styleWeight') or data.get('style_weight', 0.61)
        weirdness_constraint = data.get('weirdnessConstraint') or data.get('weirdness_constraint', 0.72)
        audio_weight = data.get('audioWeight') or data.get('audio_weight', 0.65)
        
        # Convert to float if they're strings
        try:
            style_weight = float(style_weight)
        except (ValueError, TypeError):
            style_weight = 0.61
            
        try:
            weirdness_constraint = float(weirdness_constraint)
        except (ValueError, TypeError):
            weirdness_constraint = 0.72
            
        try:
            audio_weight = float(audio_weight)
        except (ValueError, TypeError):
            audio_weight = 0.65
        
        # Validate numeric parameters
        validator = ParameterValidator()
        
        # Create optional params dict for validation
        optional_params = {
            'styleWeight': style_weight,
            'weirdnessConstraint': weirdness_constraint,
            'audioWeight': audio_weight
        }
        
        # Validate optional parameters (add-vocals doesn't use custom_mode or personaId)
        validated_optional_params, validation_error = validator.validate_optional_parameters(
            optional_params, custom_mode=False
        )
        
        if validation_error:
            return jsonify(ResponseUtils.create_error_response(validation_error)), 400
        
        # Extract validated values
        style_weight = validated_optional_params.get('styleWeight', 0.61)
        weirdness_constraint = validated_optional_params.get('weirdnessConstraint', 0.72)
        audio_weight = validated_optional_params.get('audioWeight', 0.65)
        
        # If no callback URL provided, construct default from public base URL
        if not call_back_url:
            public_base_url = Config.get_public_base_url(request)
            call_back_url = f"{public_base_url}/callback"
        
        # Initialize API client
        client = KieAPIClient()
        
        # Call Kie API to add vocals
        response = client.add_vocals(
            upload_url=upload_url,
            prompt=prompt,
            title=title,
            style=style,
            tags=tags,
            negative_tags=negative_tags,
            call_back_url=call_back_url,
            model=model,
            vocal_gender=vocal_gender,
            style_weight=style_weight,
            weirdness_constraint=weirdness_constraint,
            audio_weight=audio_weight
        )
        
        if is_successful_kie_response(response):
            record_usage('add_vocals', units=1)
            response['usage'] = usage_meta
        else:
            _, usage_meta_now, _ = check_allowed(units=0)
            response['usage'] = usage_meta_now
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error adding vocals: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/vocal-removal', methods=['POST'])
@limiter.limit("5 per minute")
def vocal_removal():
    """Separate vocal/stems from a track using Kie API."""
    try:
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Required parameters
        task_id = data.get('taskId')
        audio_id = data.get('audioId')
        separation_type = data.get('type')
        
        if not task_id:
            return jsonify(ResponseUtils.create_error_response('taskId is required')), 400
        if not audio_id:
            return jsonify(ResponseUtils.create_error_response('audioId is required')), 400
        if not separation_type:
            return jsonify(ResponseUtils.create_error_response('type is required (separate_vocal or split_stem)')), 400

        allowed, usage_meta, status_code = check_allowed(units=1)
        if not allowed:
            payload = ResponseUtils.create_error_response(usage_meta.get('error', 'Usage limit exceeded'), status_code)
            payload.update(usage_meta)
            return jsonify(payload), status_code
            
        # Optional parameter
        call_back_url = data.get('callBackUrl')
        
        # If no callback URL provided, construct default from public base URL
        if not call_back_url:
            public_base_url = Config.get_public_base_url(request)
            call_back_url = f"{public_base_url}/callback"
            
        # Initialize API client
        client = KieAPIClient()
        
        # Call Kie API
        response = client.vocal_removal(
            task_id=task_id,
            audio_id=audio_id,
            type=separation_type,
            call_back_url=call_back_url
        )
        
        if is_successful_kie_response(response):
            record_usage('vocal_removal', units=1)
            response['usage'] = usage_meta
        else:
            _, usage_meta_now, _ = check_allowed(units=0)
            response['usage'] = usage_meta_now
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error in vocal removal: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/task-status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get status of a generation task."""
    try:
        current_app.logger.info(f"Getting task status for task_id: {task_id}")
        client = KieAPIClient()
        status = client.get_task_status(task_id)
        current_app.logger.info(f"Task status response received for {task_id}")
        return jsonify(status)
    except Exception as e:
        current_app.logger.error(f"Error getting task status: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/video-status/<video_task_id>', methods=['GET'])
def get_video_status(video_task_id):
    """Get status of a video generation task from history."""
    try:
        current_app.logger.info(f"Getting video status for video_task_id: {video_task_id}")
        
        # Load history to find video callbacks
        from app.services.history_service import HistoryService
        history_service = HistoryService()
        history = history_service.load_history()
        
        # Find video callbacks for this task
        video_callbacks = []
        for entry in history:
            if entry.get('task_id') == video_task_id and entry.get('is_video_callback', False):
                video_callbacks.append(entry)
        
        if video_callbacks:
            # Sort by timestamp (newest first)
            video_callbacks.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            latest_callback = video_callbacks[0]
            
            # Extract video URL if available
            video_url = latest_callback.get('video_url')
            status_code = latest_callback.get('status_code')
            status_message = latest_callback.get('status_message')
            
            return jsonify(ResponseUtils.create_success_response({
                'video_task_id': video_task_id,
                'status': 'complete' if status_code in [0, 200] else 'processing',
                'status_code': status_code,
                'status_message': status_message,
                'video_url': video_url,
                'has_video': video_url is not None,
                'last_callback_time': latest_callback.get('timestamp'),
                'callbacks_count': len(video_callbacks)
            }))
        else:
            # Check if there's a video task in progress (no callbacks yet)
            return jsonify(ResponseUtils.create_success_response({
                'video_task_id': video_task_id,
                'status': 'processing',
                'status_code': None,
                'status_message': 'Video generation in progress',
                'video_url': None,
                'has_video': False,
                'last_callback_time': None,
                'callbacks_count': 0
            }))
            
    except Exception as e:
        current_app.logger.error(f"Error getting video status: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/models', methods=['GET'])
def get_models():
    """Get available model versions and their constraints."""
    models = ModelValidator.get_all_models()
    return jsonify(models)


@api_bp.route('/download-url', methods=['POST'])
def get_download_url():
    """Get a downloadable URL for kie.ai generated files."""
    try:
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        url = data.get('url')
        if not url:
            return jsonify(ResponseUtils.create_error_response('URL is required')), 400
        
        # Check if URL is from kie.ai services
        if not URLUtils.is_kie_cdn_url(url):
            return jsonify(ResponseUtils.create_error_response(
                'Only kie.ai/suno.ai generated file URLs are supported',
                422
            )), 422
        
        # Initialize API client
        client = KieAPIClient()
        
        # Make request to kie.ai download URL API
        endpoint = f"{client.base_url}/api/v1/common/download-url"
        
        # Use the same headers as other API calls
        response = requests.post(
            endpoint,
            headers=client.headers,
            json={'url': url},
            timeout=15
        )
        
        current_app.logger.info(f"Download URL API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            current_app.logger.info(f"Download URL API response: {jsonify(result).get_data(as_text=True)}")
            return jsonify(result)
        else:
            # If kie.ai API fails, try to get the file directly
            current_app.logger.warning(f"Kie.ai download API failed with {response.status_code}, trying direct download")
            
            # Check if it's a suno.ai CDN URL (these might work directly)
            if 'cdn1.suno.ai' in url or 'cdn2.suno.ai' in url:
                return jsonify({
                    'code': 200,
                    'msg': 'success',
                    'data': url  # Return the original URL for direct download
                })
            
            # Return the error from kie.ai API
            try:
                error_data = response.json()
                return jsonify(error_data), response.status_code
            except:
                return jsonify(ResponseUtils.create_error_response(
                    f'Failed to get download URL: {response.status_code}',
                    response.status_code
                )), response.status_code
            
    except Exception as e:
        current_app.logger.error(f"Error getting download URL: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/download-audio', methods=['POST'])
def download_audio():
    """Download audio file from kie.ai/suno.ai and stream it to user."""
    try:
        current_app.logger.info("generate_music_direct endpoint called")
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        url = data.get('url')
        filename = data.get('filename', 'audio.mp3')
        
        if not url:
            return jsonify(ResponseUtils.create_error_response('URL is required')), 400
        
        # Validate URL
        if not (url.startswith('http://') or url.startswith('https://')):
            return jsonify(ResponseUtils.create_error_response('Invalid URL format')), 400
        
        # Clean filename for safety
        filename = FileUtils.get_safe_filename(filename)
        
        current_app.logger.info(f"Downloading audio from {url} as {filename}")
        
        # Set up headers for the request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Add API key for kie.ai URLs if available
        if 'kie.ai' in url:
            client = KieAPIClient()
            if client.api_key and not client.use_mock:
                headers['Authorization'] = f'Bearer {client.api_key}'
        
        # Stream the download
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        
        if response.status_code != 200:
            current_app.logger.error(f"Failed to download audio: {response.status_code}")
            return jsonify(ResponseUtils.create_error_response(
                f'Failed to download audio: HTTP {response.status_code}',
                response.status_code
            )), response.status_code
        
        # Create a streaming response
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        
        # Determine content type
        content_type = response.headers.get('Content-Type', 'audio/mpeg')
        
        return Response(
            generate(),
            mimetype=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': response.headers.get('Content-Length', ''),
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
        
    except requests.exceptions.Timeout:
        current_app.logger.error("Download request timed out")
        return jsonify(ResponseUtils.create_error_response('Download request timed out')), 504
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Download request failed: {e}")
        return jsonify(ResponseUtils.create_error_response(f'Download failed: {str(e)}')), 500
    except Exception as e:
        current_app.logger.error(f"Error downloading audio: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/templates', methods=['GET'])
def get_templates():
    """Get music generation templates with filtering and sorting options."""
    try:
        from app.services.template_service import TemplateService
        
        # Get query parameters
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        difficulty = request.args.get('difficulty')
        search = request.args.get('search')
        tags = request.args.getlist('tag')  # Multiple tags can be passed as ?tag=electronic&tag=chill
        sort_by = request.args.get('sort_by', 'popularity')
        sort_order = request.args.get('sort_order', 'desc')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Parse min/max popularity
        min_popularity = request.args.get('min_popularity')
        max_popularity = request.args.get('max_popularity')
        min_popularity = int(min_popularity) if min_popularity and min_popularity.isdigit() else None
        max_popularity = int(max_popularity) if max_popularity and max_popularity.isdigit() else None
        
        # Parse instrumental filter
        instrumental = request.args.get('instrumental')
        instrumental = instrumental.lower() == 'true' if instrumental else None
        
        # Initialize template service
        template_service = TemplateService()
        
        # Apply filters
        if search:
            templates = template_service.search_templates(search)
        else:
            templates = template_service.filter_templates(
                category=category,
                subcategory=subcategory,
                difficulty=difficulty,
                min_popularity=min_popularity,
                max_popularity=max_popularity,
                tags=tags if tags else None,
                instrumental=instrumental
            )
        
        # Sort templates
        templates = template_service.sort_templates(templates, sort_by=sort_by, sort_order=sort_order)
        
        # Apply pagination
        total_templates = len(templates)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_templates = templates[start_idx:end_idx]
        
        # Get template statistics
        stats = template_service.get_template_stats()
        
        # Get available categories and tags for filtering UI
        categories = template_service.get_categories()
        all_tags = template_service.get_tags()
        
        return jsonify(ResponseUtils.create_success_response({
            'templates': paginated_templates,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_templates,
                'total_pages': (total_templates + per_page - 1) // per_page,
                'has_next': end_idx < total_templates,
                'has_prev': page > 1
            },
            'filters': {
                'available_categories': categories,
                'available_tags': all_tags,
                'applied_filters': {
                    'category': category,
                    'subcategory': subcategory,
                    'difficulty': difficulty,
                    'search': search,
                    'tags': tags,
                    'min_popularity': min_popularity,
                    'max_popularity': max_popularity,
                    'instrumental': instrumental,
                    'sort_by': sort_by,
                    'sort_order': sort_order
                }
            },
            'stats': stats
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error getting templates: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/templates/<template_id>', methods=['GET'])
def get_template_by_id(template_id):
    """Get a specific template by ID."""
    try:
        from app.services.template_service import TemplateService
        
        template_service = TemplateService()
        template = template_service.get_template_by_id(template_id)
        
        if not template:
            return jsonify(ResponseUtils.create_error_response(f'Template not found: {template_id}')), 404
        
        return jsonify(ResponseUtils.create_success_response({
            'template': template
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error getting template by ID: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/templates/categories', methods=['GET'])
def get_template_categories():
    """Get all available template categories and subcategories."""
    try:
        from app.services.template_service import TemplateService
        
        template_service = TemplateService()
        categories = template_service.get_categories()
        
        # Get subcategories for each category
        categories_with_subcategories = []
        for category in categories:
            subcategories = template_service.get_subcategories(category=category)
            categories_with_subcategories.append({
                'category': category,
                'subcategories': subcategories,
                'count': len(template_service.get_templates_by_category(category))
            })
        
        return jsonify(ResponseUtils.create_success_response({
            'categories': categories_with_subcategories
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error getting template categories: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/templates/stats', methods=['GET'])
def get_template_stats():
    """Get template statistics."""
    try:
        from app.services.template_service import TemplateService
        
        template_service = TemplateService()
        stats = template_service.get_template_stats()
        
        return jsonify(ResponseUtils.create_success_response({
            'stats': stats
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error getting template stats: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/user-activity', methods=['GET'])
def get_user_activity():
    """Get recent user activities aggregated from history system."""
    try:
        from flask_login import current_user
        from app.services.history_service import HistoryService
        from app.core.utils import DateTimeUtils
        from datetime import datetime, timedelta
        
        # Check authentication
        if not current_user.is_authenticated:
            return jsonify(ResponseUtils.create_error_response('Authentication required')), 401
        
        # Get query parameters
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        activity_type = request.args.get('type')
        days_back = int(request.args.get('days', 30))
        
        # Initialize history service
        history_service = HistoryService()
        history = history_service.load_history()
        
        # Helper functions
        def get_activity_description(entry, entry_type):
            """Generate human-readable description for activity."""
            task_id = entry.get('task_id', '')[:8]
            
            if entry_type == 'video_processing':
                return f"Completed video generation for task {task_id}"
            elif entry_type == 'generation_complete':
                return f"Completed audio generation for task {task_id}"
            elif entry_type == 'processing':
                status = entry.get('status', 'processing')
                return f"Task {task_id} is {status}"
            elif entry_type == 'upload':
                return f"Uploaded audio for processing"
            else:
                return f"Performed system activity"
        
        def is_within_last_24_hours(timestamp_str):
            """Check if timestamp is within last 24 hours."""
            timestamp = DateTimeUtils.parse_timestamp(timestamp_str)
            if not timestamp:
                return False
            
            cutoff = datetime.utcnow() - timedelta(hours=24)
            return timestamp > cutoff
        
        def count_activities_by_type(activities_list):
            """Count activities by type."""
            counts = {}
            for activity in activities_list:
                activity_type = activity['type']
                counts[activity_type] = counts.get(activity_type, 0) + 1
            return counts
        
        # Process history entries into activity format
        activities = []
        for entry in history:
            # **KEY FIX: Filter by current user**
            entry_user_id = str(entry.get('user_id', ''))
            current_user_id = str(current_user.id)
            if entry_user_id != current_user_id:
                continue
            
            # Skip entries without timestamps
            timestamp = entry.get('timestamp')
            if not timestamp:
                continue
            
            # Check if entry is within time range
            if days_back > 0:
                entry_time = DateTimeUtils.parse_timestamp(timestamp)
                if not entry_time:
                    continue
                cutoff = datetime.utcnow() - timedelta(days=days_back)
                if entry_time < cutoff:
                    continue
            
            # Determine activity type
            if entry.get('is_video_callback', False):
                entry_type = 'video_processing'
            elif entry.get('status_code') == 200:
                entry_type = 'generation_complete'
            elif 'task_id' in entry and 'status' in entry:
                entry_type = 'processing'
            elif 'upload_url' in entry:
                entry_type = 'upload'
            else:
                entry_type = 'system'
            
            # Filter by activity type if specified
            if activity_type and entry_type != activity_type:
                continue
            
            # Derive human-readable title
            type_titles = {
                'generation_complete': 'Music Generated',
                'video_processing': 'Video Created',
                'processing': 'Task Processing',
                'upload': 'Audio Uploaded',
                'system': 'System Event',
            }
            entry_title = type_titles.get(entry_type, 'Activity')
            
            # Derive status string
            type_statuses = {
                'generation_complete': 'success',
                'video_processing': 'success',
                'upload': 'success',
                'processing': 'processing',
                'system': 'info',
            }
            entry_status = type_statuses.get(entry_type, 'info')
            
            # Create activity object
            activity = {
                'id': entry.get('id', ''),
                'type': entry_type,
                'title': entry_title,
                'status': entry_status,
                'description': get_activity_description(entry, entry_type),
                'timestamp': timestamp,
                'task_id': entry.get('task_id'),
                'metadata': {
                    'task_id': entry.get('task_id'),
                    'status_code': entry.get('status_code'),
                    'status_message': entry.get('status_message'),
                    'is_video': entry.get('is_video_callback', False),
                    'has_audio_url': 'audio_url' in entry,
                    'has_video_url': 'video_url' in entry
                }
            }
            
            activities.append(activity)
        
        # Sort by timestamp (newest first)
        activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply pagination
        total_activities = len(activities)
        paginated_activities = activities[offset:offset + limit]
        
        # Format timestamps for display
        for activity in paginated_activities:
            activity['time_ago'] = DateTimeUtils.format_time_ago(activity['timestamp'])
        
        return jsonify(ResponseUtils.create_success_response({
            'activities': paginated_activities,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': total_activities,
                'has_more': (offset + limit) < total_activities
            },
            'summary': {
                'total_activities': total_activities,
                'last_24_hours': len([a for a in activities if is_within_last_24_hours(a['timestamp'])]),
                'by_type': count_activities_by_type(activities)
            }
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error getting user activity: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/recent-creations', methods=['GET'])
def get_recent_creations():
    """Get the current user's most recent track creations for the dashboard gallery."""
    try:
        from flask_login import current_user
        from app.services.history_service import HistoryService
        from app.core.utils import DateTimeUtils

        if not current_user.is_authenticated:
            return jsonify(ResponseUtils.create_error_response('Authentication required')), 401

        limit = int(request.args.get('limit', 6))

        history_service = HistoryService()
        history = history_service.load_history()

        # Collect the most recent successful generation entries for this user
        creations = []
        for entry in history:
            if str(entry.get('user_id', '')) != str(current_user.id):
                continue
            if entry.get('status_code') != 200:
                continue
            processed_data = entry.get('processed_data') or {}
            tracks = processed_data.get('tracks', [])
            if not tracks:
                continue
            timestamp = entry.get('timestamp', '')
            for track in tracks:
                image_urls = track.get('image_urls') or {}
                image_url = (
                    image_urls.get('default') or
                    image_urls.get('small') or
                    image_urls.get('large') or
                    track.get('image_url') or
                    None
                )
                audio_urls = track.get('audio_urls') or {}
                audio_url = (
                    audio_urls.get('mp3_128') or
                    audio_urls.get('mp3_64') or
                    audio_urls.get('default') or
                    track.get('audio_url') or
                    None
                )
                creations.append({
                    'id': track.get('id', entry.get('id', '')),
                    'title': track.get('title') or 'Untitled',
                    'artist': track.get('model_name') or 'AI Generated',
                    'duration': track.get('duration') or 0,
                    'image_url': image_url,
                    'audio_url': audio_url,
                    'timestamp': timestamp,
                    'time_ago': DateTimeUtils.format_time_ago(timestamp) if timestamp else '',
                    'tags': track.get('tags', ''),
                })

        # Sort newest first and limit
        creations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        creations = creations[:limit]

        return jsonify(ResponseUtils.create_success_response({
            'creations': creations,
            'total': len(creations)
        }))

    except Exception as e:
        current_app.logger.error(f"Error getting recent creations: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/songs/promoted', methods=['GET'])
def get_promoted_songs():
    """Get promoted songs from history (all users)."""
    try:
        from app.services.history_service import HistoryService
        from app.core.utils import DateTimeUtils
        from datetime import datetime
        
        # Get query parameters
        limit = int(request.args.get('limit', 12))
        offset = int(request.args.get('offset', 0))
        
        # Initialize history service
        history_service = HistoryService()
        history = history_service.load_history()
        
        # Collect tracks from successful generation entries with timestamps
        songs_with_ts = []
        for entry in history:
            # Skip non-successful entries
            if entry.get('status_code') != 200:
                continue
            # Skip entries without processed_data
            processed_data = entry.get('processed_data', {})
            if not processed_data:
                continue
            # Get entry timestamp for sorting
            entry_timestamp = entry.get('timestamp')
            # Parse timestamp to datetime object for sorting
            entry_dt = DateTimeUtils.parse_timestamp(entry_timestamp) if entry_timestamp else None
            
            # Get tracks
            tracks = processed_data.get('tracks', [])
            for track in tracks:
                # Ensure artist is not None
                artist = track.get('model_name')
                if not artist or artist == 'None':
                    artist = 'AI Generated'
                # Ensure duration is numeric
                duration = track.get('duration')
                if duration is None:
                    duration = 0
                # Transform track to song format expected by frontend
                song = {
                    'title': track.get('title', 'Untitled'),
                    'artist': artist,
                    'duration': duration,
                    'id': track.get('id', ''),
                    'audio_urls': track.get('audio_urls', {}),
                    'image_urls': track.get('image_urls', {}),
                    'tags': track.get('tags', ''),
                    'prompt': track.get('prompt', ''),
                    'model_name': track.get('model_name', '')
                }
                songs_with_ts.append((entry_dt, song))
        
        # Sort by timestamp descending (newest first)
        # Entries without timestamp go last
        songs_with_ts.sort(key=lambda x: x[0] or datetime.min, reverse=True)
        songs = [song for _, song in songs_with_ts]
        
        # Apply pagination
        total = len(songs)
        paginated_songs = songs[offset:offset + limit]
        
        return jsonify(ResponseUtils.create_success_response({
            'songs': paginated_songs,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': total,
                'has_more': (offset + limit) < total
            }
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error getting promoted songs: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/projects', methods=['GET'])
def get_user_projects():
    """Get all projects for the current user."""
    try:
        from flask_login import current_user
        from app.models import Project
        
        if not current_user.is_authenticated:
            return jsonify(ResponseUtils.create_error_response('Authentication required')), 401
        
        # Get query parameters
        project_type = request.args.get('type')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        archived = request.args.get('archived')
        
        # Build query
        query = Project.query.filter_by(user_id=current_user.id)
        
        if project_type:
            query = query.filter_by(project_type=project_type)
        
        if archived is not None:
            is_archived = archived.lower() == 'true'
            query = query.filter_by(is_archived=is_archived)
        
        # Order by most recent
        query = query.order_by(Project.updated_at.desc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        projects = query.offset(offset).limit(limit).all()
        
        return jsonify(ResponseUtils.create_success_response({
            'projects': [project.to_dict() for project in projects],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total
            }
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error getting user projects: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/projects', methods=['POST'])
def create_project():
    """Create a new project."""
    try:
        from flask_login import current_user
        from app.models import Project, db
        
        if not current_user.is_authenticated:
            return jsonify(ResponseUtils.create_error_response('Authentication required')), 401
        
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Required fields
        title = data.get('title')
        if not title:
            return jsonify(ResponseUtils.create_error_response('Title is required')), 400
        
        # Optional fields
        description = data.get('description')
        project_type = data.get('project_type', 'lyrics')
        lyrics_data = data.get('lyrics_data')
        music_data = data.get('music_data')
        tags = data.get('tags', [])
        is_public = data.get('is_public', False)
        
        # Create project
        project = Project(
            user_id=current_user.id,
            title=title,
            project_type=project_type,
            description=description,
            lyrics_data=lyrics_data,
            music_data=music_data,
            tags=tags,
            is_public=is_public
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify(ResponseUtils.create_success_response({
            'project': project.to_dict(),
            'message': 'Project created successfully'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error creating project: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project by ID."""
    try:
        from flask_login import current_user
        from app.models import Project
        
        if not current_user.is_authenticated:
            return jsonify(ResponseUtils.create_error_response('Authentication required')), 401
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify(ResponseUtils.create_error_response('Project not found')), 404
        
        # Check permissions
        if project.user_id != current_user.id and not project.is_public:
            return jsonify(ResponseUtils.create_error_response('Access denied')), 403
        
        return jsonify(ResponseUtils.create_success_response({
            'project': project.to_dict()
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error getting project: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update a project."""
    try:
        from flask_login import current_user
        from app.models import Project, db
        
        if not current_user.is_authenticated:
            return jsonify(ResponseUtils.create_error_response('Authentication required')), 401
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify(ResponseUtils.create_error_response('Project not found')), 404
        
        # Check ownership
        if project.user_id != current_user.id:
            return jsonify(ResponseUtils.create_error_response('Access denied')), 403
        
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Update fields
        if 'title' in data:
            project.title = data['title']
        
        if 'description' in data:
            project.description = data['description']
        
        if 'project_type' in data:
            project.project_type = data['project_type']
        
        if 'lyrics_data' in data:
            project.lyrics_data = data['lyrics_data']
        
        if 'music_data' in data:
            project.music_data = data['music_data']
        
        if 'tags' in data:
            project.tags = data['tags']
        
        if 'is_public' in data:
            project.is_public = data['is_public']
        
        if 'is_archived' in data:
            project.is_archived = data['is_archived']
        
        db.session.commit()
        
        return jsonify(ResponseUtils.create_success_response({
            'project': project.to_dict(),
            'message': 'Project updated successfully'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error updating project: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project."""
    try:
        from flask_login import current_user
        from app.models import Project, db
        
        if not current_user.is_authenticated:
            return jsonify(ResponseUtils.create_error_response('Authentication required')), 401
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify(ResponseUtils.create_error_response('Project not found')), 404
        
        # Check ownership
        if project.user_id != current_user.id:
            return jsonify(ResponseUtils.create_error_response('Access denied')), 403
        
        db.session.delete(project)
        db.session.commit()
        
        return jsonify(ResponseUtils.create_success_response({
            'message': 'Project deleted successfully'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting project: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/projects/<project_id>/lyrics', methods=['PUT'])
def update_project_lyrics(project_id):
    """Update lyrics data in a project."""
    try:
        from flask_login import current_user
        from app.models import Project, db
        
        if not current_user.is_authenticated:
            return jsonify(ResponseUtils.create_error_response('Authentication required')), 401
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify(ResponseUtils.create_error_response('Project not found')), 404
        
        # Check ownership
        if project.user_id != current_user.id:
            return jsonify(ResponseUtils.create_error_response('Access denied')), 403
        
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        lyrics_data = data.get('lyrics_data')
        if lyrics_data is None:
            return jsonify(ResponseUtils.create_error_response('lyrics_data is required')), 400
        
        # Update lyrics
        project.update_lyrics(lyrics_data)
        db.session.commit()
        
        return jsonify(ResponseUtils.create_success_response({
            'project': project.to_dict(),
            'message': 'Lyrics updated successfully'
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error updating project lyrics: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500


@api_bp.route('/save-lyrics', methods=['POST'])
def save_lyrics():
    """Save lyrics to a project (creates new project or updates existing)."""
    try:
        from flask_login import current_user
        from app.models import Project, db
        
        if not current_user.is_authenticated:
            return jsonify(ResponseUtils.create_error_response('Authentication required')), 401
        
        data = request.json
        if not data:
            return jsonify(ResponseUtils.create_error_response('No JSON data provided')), 400
        
        # Required fields
        lyrics_data = data.get('lyrics_data')
        title = data.get('title')
        
        if not lyrics_data:
            return jsonify(ResponseUtils.create_error_response('lyrics_data is required')), 400
        
        if not title:
            return jsonify(ResponseUtils.create_error_response('title is required')), 400
        
        # Optional fields
        project_id = data.get('project_id')
        description = data.get('description', '')
        tags = data.get('tags', [])
        is_public = data.get('is_public', False)
        
        if project_id:
            # Update existing project
            project = Project.query.get(project_id)
            if not project:
                return jsonify(ResponseUtils.create_error_response('Project not found')), 404
            
            # Check ownership
            if project.user_id != current_user.id:
                return jsonify(ResponseUtils.create_error_response('Access denied')), 403
            
            project.title = title
            project.description = description
            project.tags = tags
            project.is_public = is_public
            project.update_lyrics(lyrics_data)
            
            message = 'Lyrics updated in existing project'
        else:
            # Create new project
            project = Project(
                user_id=current_user.id,
                title=title,
                project_type='lyrics',
                description=description,
                lyrics_data=lyrics_data,
                tags=tags,
                is_public=is_public
            )
            db.session.add(project)
            message = 'Lyrics saved to new project'
        
        db.session.commit()
        
        return jsonify(ResponseUtils.create_success_response({
            'project': project.to_dict(),
            'message': message
        }))
        
    except Exception as e:
        current_app.logger.error(f"Error saving lyrics: {e}")
        return jsonify(ResponseUtils.create_error_response(str(e))), 500