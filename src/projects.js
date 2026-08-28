const crypto = require('node:crypto');
const { readJson, writeJson } = require('./persistence');

async function getProjects(userId) { const projects = await readJson('projects.json', {}); return projects[String(userId)] ?? {}; }
async function saveProjects(userId, userProjects) { const projects = await readJson('projects.json', {}); projects[String(userId)] = userProjects; await writeJson('projects.json', projects); }
async function createProject(userId, fields) { const projects = await getProjects(userId); const id = crypto.randomUUID(); projects[id] = { id, name: fields.name, description: fields.description ?? '', status: fields.status ?? 'Active', wordcount: Number(fields.wordcount ?? 0), goal: fields.goal === '' ? null : Number(fields.goal ?? 0), created_at: new Date().toISOString() }; await saveProjects(userId, projects); return projects[id]; }
async function updateProject(userId, projectId, changes) { const projects = await getProjects(userId); if (!projects[projectId]) return null; Object.assign(projects[projectId], changes); await saveProjects(userId, projects); return projects[projectId]; }
module.exports = { createProject, getProjects, updateProject };