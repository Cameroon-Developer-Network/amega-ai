# Contributing to Amega AI

<div align="center">
  <img src="https://img.shields.io/badge/Contributions-Welcome-brightgreen.svg" alt="Contributions Welcome">
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen.svg" alt="PRs Welcome">
</div>

Thank you for your interest in contributing to Amega AI! This document provides guidelines and best practices for contributing to our project.

## 📋 Table of Contents
- [Branch Management Guidelines](#branch-management-guidelines)
- [Best Practices](#best-practices)
- [Getting Started](#getting-started)
- [Questions](#questions)

## Branch Management Guidelines

### Branch Structure

We follow a simple branching model with two main branches and several supporting branches:

```
main (production) ──────┐
                       │
develop (development) ─┼─────┐
                       │     │
                       │     ├── feature/* (new features)
                       │     │
                       │     ├── bugfix/* (bug fixes)
                       │     │
                       │     ├── release/* (release preparation)
                       │     │
                       │     └── hotfix/* (urgent fixes)
                       │
                       └─────┘
```

Here's what each branch is for:

1. **main branch** (production)
   - This is where the stable, production-ready code lives
   - Only tested and approved code goes here
   - Each commit here should be tagged with a version number (like v1.0.0)

2. **develop branch** (development)
   - This is where all new development happens
   - All new features and bug fixes start here
   - This branch is always ahead of main

3. **feature branches** (feature/*)
   - Created from develop branch
   - Used for developing new features
   - Example: `feature/chat-interface`, `feature/user-authentication`
   - When done, merged back into develop

4. **bugfix branches** (bugfix/*)
   - Created from develop branch
   - Used to fix bugs found during development
   - Example: `bugfix/login-error`, `bugfix/api-timeout`
   - When fixed, merged back into develop

5. **release branches** (release/*)
   - Created from develop when preparing a new release
   - Used for final testing and small fixes before release
   - Example: `release/v1.1.0`
   - When ready, merged into both main and develop

6. **hotfix branches** (hotfix/*)
   - Created from main branch
   - Used for urgent fixes needed in production
   - Example: `hotfix/security-patch`
   - When fixed, merged into both main and develop

---

### Best Practices

1. **Branch Naming**:
   - Use descriptive, lowercase names with hyphens
   - Follow the prefix conventions strictly
   - Keep branch names concise but meaningful

2. **Commit Messages**:
   - Write clear, descriptive commit messages
   - Use present tense
   - Reference issue numbers when applicable

3. **Pull Requests**:
   - Create PRs early for visibility
   - Include clear descriptions of changes
   - Request reviews from relevant team members
   - Ensure all tests pass before merging

4. **Code Review**:
   - Review PRs promptly
   - Provide constructive feedback
   - Ensure code meets project standards

5. **Branch Cleanup**:
   - Delete branches after merging
   - Keep the repository clean and organized

---

### Getting Started

1. Fork the repository
2. Clone your fork
3. Create a new branch following the naming conventions
4. Make your changes
5. Submit a pull request

---

### Questions?

If you have any questions about contributing, please open an issue in the repository or contact the maintainers.

<div align="center">
  <h3>Thank you for contributing to Amega AI! 🎉</h3>
</div>