import { useNavigate } from 'react-router-dom'

import { Badge, Button, Card } from '../../../components/ui'

function OverviewPage() {
    const navigate = useNavigate()

    return (
        <main>
            <h1>RepoGuard-Eval</h1>

            <p>
                Evidence-based evaluation benchmark for AI-powered Go
                repository debugging.
            </p>

            <Card className="overview-foundation-card">
                <Badge variant="success">Frontend foundation</Badge>

                <h2>Application foundation initialized</h2>

                <p>
                    The application shell, routing, state management, and
                    design system are in place.
                </p>

                <Button
                    variant="secondary"
                    onClick={() => navigate('/documentation')}
                >
                    View documentation
                </Button>
            </Card>
        </main>
    )
}

export default OverviewPage