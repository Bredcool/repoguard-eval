import EmptyState from '../../../components/feedback/EmptyState'

function RepositoriesPage() {
    return (
        <section>
            <h1>Repositories</h1>

            <p>
                Manage source repositories used by RepoGuard-Eval.
            </p>

            <EmptyState
                title="No repositories yet"
                description="Repository management will be available in a future implementation phase."
            />
        </section>
    )
}

export default RepositoriesPage