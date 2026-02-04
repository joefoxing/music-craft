import os
import json
from typing import List, Dict, Any, Optional
from flask import current_app
from app.core.utils import JSONUtils

class TemplateService:
    """
    Service to manage music generation templates and playlist templates.
    """
    
    def __init__(self):
        self.templates_file = self._get_templates_file_path()
        self._templates_cache = None

    def _get_templates_file_path(self) -> str:
        """Get the path to the templates JSON file."""
        try:
            return os.path.join(current_app.root_path, 'static', 'templates', 'templates.json')
        except RuntimeError:
            # Fallback for testing outside Flask context
            return os.path.join('app', 'static', 'templates', 'templates.json')

    def get_all_templates(self) -> List[Dict[str, Any]]:
        """Get all templates."""
        if self._templates_cache is not None:
            return self._templates_cache
            
        data = JSONUtils.load_json_file(self.templates_file, {"templates": []})
        templates = data.get("templates", [])
        self._templates_cache = templates
        return templates

    def search_templates(self, query: str) -> List[Dict[str, Any]]:
        """Search templates by name, description, or tags."""
        templates = self.get_all_templates()
        if not query:
            return templates
            
        query = query.lower()
        results = []
        for template in templates:
            if (query in template.get('name', '').lower() or 
                query in template.get('description', '').lower() or 
                query in template.get('style', '').lower() or
                any(query in tag.lower() for tag in template.get('tags', []))):
                results.append(template)
        return results

    def filter_templates(self, category: str = None, subcategory: str = None, 
                        difficulty: str = None, min_popularity: int = None, 
                        max_popularity: int = None, tags: List[str] = None,
                        instrumental: bool = None) -> List[Dict[str, Any]]:
        """Filter templates by various criteria."""
        templates = self.get_all_templates()
        filtered = []
        
        for template in templates:
            if category and template.get('category') != category:
                continue
            if subcategory and template.get('subcategory') != subcategory:
                continue
            if difficulty and template.get('difficulty') != difficulty:
                continue
            if min_popularity is not None and template.get('popularity', 0) < min_popularity:
                continue
            if max_popularity is not None and template.get('popularity', 0) > max_popularity:
                continue
            if instrumental is not None and template.get('instrumental') != instrumental:
                continue
            if tags:
                template_tags = set(t.lower() for t in template.get('tags', []))
                if not any(tag.lower() in template_tags for tag in tags):
                    continue
            
            filtered.append(template)
            
        return filtered

    def sort_templates(self, templates: List[Dict[str, Any]], sort_by: str = 'popularity', 
                      sort_order: str = 'desc') -> List[Dict[str, Any]]:
        """Sort templates."""
        reverse = sort_order == 'desc'
        
        def get_sort_key(t):
            return t.get(sort_by, 0) if sort_by != 'name' else t.get('name', '')
            
        return sorted(templates, key=get_sort_key, reverse=reverse)

    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a template by ID."""
        templates = self.get_all_templates()
        for template in templates:
            if template.get('id') == template_id:
                return template
        return None

    def get_categories(self) -> List[str]:
        """Get list of unique categories."""
        templates = self.get_all_templates()
        return sorted(list(set(t.get('category') for t in templates if t.get('category'))))

    def get_subcategories(self, category: str = None) -> List[str]:
        """Get list of unique subcategories, optionally filtered by category."""
        templates = self.get_all_templates()
        subcategories = set()
        for t in templates:
            if category and t.get('category') != category:
                continue
            if t.get('subcategory'):
                subcategories.add(t.get('subcategory'))
        return sorted(list(subcategories))

    def get_tags(self) -> List[str]:
        """Get list of all unique tags."""
        templates = self.get_all_templates()
        tags = set()
        for t in templates:
            for tag in t.get('tags', []):
                tags.add(tag)
        return sorted(list(tags))

    def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all templates in a category."""
        return self.filter_templates(category=category)

    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about templates."""
        templates = self.get_all_templates()
        categories = self.get_categories()
        
        return {
            'total_count': len(templates),
            'category_counts': {cat: len(self.get_templates_by_category(cat)) for cat in categories},
            'avg_popularity': sum(t.get('popularity', 0) for t in templates) / len(templates) if templates else 0
        }

    def clear_cache(self):
        """Clear the templates cache."""
        self._templates_cache = None

    # --- Legacy/Playlist methods ---

    def parse_template(self, template_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates and parses the template JSON schema for playlists.
        """
        required_fields = ['id', 'name', 'nodes']
        for field in required_fields:
            if field not in template_json:
                raise ValueError(f"Invalid template: missing '{field}' field")
        return template_json

    def resolve_constraints(self, template: Dict[str, Any], base_theme: str) -> List[Dict[str, Any]]:
        """
        Resolves the template nodes into a linear sequence of generation tasks.
        """
        nodes = sorted(template.get('nodes', []), key=lambda x: x.get('position', 0))
        resolved_tracks = []
        previous_track_params = {}
        
        for i, node in enumerate(nodes):
            constraints = node.get('constraints', {})
            resolved_params = {
                'position': node.get('position'),
                'role': node.get('role'),
                'prompt': f"{base_theme}, {constraints.get('prompt_suffix', '')}".strip(', '),
                'bpm': self._resolve_numeric_constraint(constraints.get('bpm'), previous_track_params.get('bpm')),
                'energy': self._resolve_numeric_constraint(constraints.get('energy'), previous_track_params.get('energy')),
            }
            resolved_tracks.append(resolved_params)
            previous_track_params = resolved_params
            
        return resolved_tracks

    def _resolve_numeric_constraint(self, constraint: Optional[Dict[str, Any]], previous_value: Optional[float]) -> Optional[float]:
        """Helper to resolve numeric values."""
        if not constraint:
            return None
        mode = constraint.get('mode', 'absolute')
        if mode == 'absolute':
            return constraint.get('value')
        elif mode == 'relative':
            if previous_value is None:
                return constraint.get('value')
            operation = constraint.get('operation', 'add')
            value = constraint.get('value', 0)
            if operation == 'add':
                return previous_value + value
            elif operation == 'multiply':
                return previous_value * value
        return constraint.get('value')
