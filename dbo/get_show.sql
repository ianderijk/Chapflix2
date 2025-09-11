select s.show
	,s.season
	,s.episode
from history h
left join shows s on h.file_key = s.file_key
where s.show = selection
order by h.time desc
limit 1;