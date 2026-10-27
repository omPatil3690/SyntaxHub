from services.agent.templates import apply_template, has_template


def test_middleware_rename_template():
    old = 'export function middleware(request) {\n  return NextResponse.next();\n}\n'
    result = apply_template("middleware.ts convention", old)
    assert "function proxy(" in result.new_content
    assert "function middleware(" not in result.new_content
    assert result.suggested_new_filename == "proxy.ts"


def test_reactdom_render_template():
    old = 'import ReactDOM from "react-dom";\n\nReactDOM.render(<App />, document.getElementById("root"));\n'
    result = apply_template("ReactDOM.render", old)
    assert "react-dom/client" in result.new_content
    assert "createRoot(document.getElementById(\"root\")).render(<App />)" in result.new_content
    assert "ReactDOM.render(" not in result.new_content


def test_reactdom_hydrate_template():
    old = 'import ReactDOM from "react-dom";\n\nReactDOM.hydrate(<App />, container);\n'
    result = apply_template("ReactDOM.hydrate", old)
    assert "hydrateRoot(container, <App />)" in result.new_content


def test_has_template_reports_correctly():
    assert has_template("middleware.ts convention") is True
    assert has_template("some unknown api") is False
