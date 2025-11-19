```
mkdir agent-webapp
cd agent-webapp
azd init -t https://github.com/azure-ai-foundry/foundry-agent-webapp
```

Configure environment variables:
```
azd env set AI_FOUNDRY_RESOURCE_GROUP zava-ignite
azd env set AI_FOUNDRY_RESOURCE_NAME zava-demo
azd env set AI_AGENT_ID BasicSupportAgent
```


```
You are a support agent that answers custom questions about our products.

Always speak in a professional tone. 
Always refer to the user by name if provided.
```

```

```