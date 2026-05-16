import re
from pathlib import Path
from .base_migrator import BaseMigrator, MigrationResult
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ReactHooksMigrator(BaseMigrator):
    @property
    def name(self) -> str:
        return "react-hooks"

    @property
    def description(self) -> str:
        return "Converts React Class Components to Functional Components with Hooks."

    @property
    def supported_extensions(self):
        return [".jsx", ".tsx", ".js", ".ts"]

    @property
    def tags(self):
        return ["react", "hooks", "frontend", "javascript"]

    def can_migrate(self, file_path: Path) -> bool:
        return file_path.suffix in self.supported_extensions

    def migrate(self, content: str, file_path: Path) -> str:
        # 1. Check for Class Component
        class_regex = re.compile(r'class\s+(\w+)\s+extends\s+(?:React\.)?Component\s*{')
        match = class_regex.search(content)
        
        if not match:
            logger.debug("No class component found in %s", file_path.name)
            return content

        component_name = match.group(1)
        logger.info("Migrating component: %s in %s", component_name, file_path.name)

        # 2. Extract render method
        # This is a naive regex for POC. Production would use tree-sitter or babel.
        render_start_match = re.search(r'render\s*\(\)\s*{', content)
        
        if not render_start_match:
            logger.warning(f"Could not find render method in {component_name}")
            return content

        start_index = render_start_match.end()
        brace_count = 1
        i = start_index
        
        while i < len(content) and brace_count > 0:
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
            i += 1
            
        if brace_count > 0:
             logger.warning("Could not find closing brace for render method")
             return content
             
        render_body = content[start_index:i-1].strip()
        
        # 3. Handle 'this.props' -> 'props'
        new_render_body = render_body.replace('this.props', 'props')
        
        # 4. Handle state (Simple counter example)
        # this.state = { count: 0 } -> const [count, setCount] = useState(0);
        # This part is complex w/o AST. We will just add a TODO comment for state
        state_migration_note = ""
        if "this.state" in content:
            state_migration_note = "\n  // TODO: Migrate state manually or use advanced ast-migrator\n  // const [state, setState] = useState(initialState);"

        # 5. Construct Functional Component
        new_content = f"""import React, {{ useState, useEffect }} from 'react';

const {component_name} = (props) => {{
{state_migration_note}

  {new_render_body}
}};

export default {component_name};
"""
        return new_content
