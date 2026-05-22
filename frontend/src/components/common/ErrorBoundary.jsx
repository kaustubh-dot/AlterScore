import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = "/";
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary-screen">
          <div className="error-boundary-card">
            <div className="error-boundary-eyebrow">SYSTEM FAULT DETECTED</div>
            <h1 className="error-boundary-title">
              CRITICAL <span>EXCEPTION</span>
            </h1>
            <p className="error-boundary-subtitle">
              An unexpected runtime error has interrupted the AlterScore pipeline. 
              The transaction has been halted to preserve state integrity.
            </p>
            
            {this.state.error && (
              <div className="error-boundary-box">
                <span className="error-boundary-type">{this.state.error.name || "Error"}</span>
                <span className="error-boundary-message">{this.state.error.message}</span>
                
                {this.state.errorInfo && (
                  <details className="error-boundary-details">
                    <summary className="error-boundary-summary">View Stack Trace</summary>
                    <pre className="error-boundary-pre">
                      {this.state.error.stack || "No stack trace available"}
                      {"\n\nComponent Stack:\n"}
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}

            <div className="error-boundary-actions">
              <button onClick={this.handleReset} className="error-boundary-button">
                RESET CORE SYSTEM
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
