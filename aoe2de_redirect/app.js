const express = require('express')
const app = express()
const port = 80

app.get('/', (req, res) => {
	aoe_link_number = req.query.gameId
	spectate = req.query.spectate
	if (spectate=='1') res.redirect('aoe2de://1/'+aoe_link_number) 
	else res.redirect('aoe2de://0/'+aoe_link_number)
})

app.listen(port, () => {
  console.log(`AoE redirect listening on port ${port}`)
})
