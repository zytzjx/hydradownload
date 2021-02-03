package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"os"

	"github.com/juju/fslock"
	cmc "github.com/zytzjx/anthenacmc/cmcserverinfo"
	"github.com/zytzjx/anthenacmc/cmcupdate"
	dmc "github.com/zytzjx/anthenacmc/datacentre"
	Log "github.com/zytzjx/anthenacmc/loggersys"
	_ "github.com/zytzjx/anthenacmc/loggersys"
	"github.com/zytzjx/anthenacmc/utils"
)

// CreateClientStatus for next
func CreateClientStatus() error {
	var cliinfo cmcupdate.ClientInfo

	jsonFile, err := os.Open("serialconfig.json")
	// if we os.Open returns an error then handle it
	if err != nil {
		Log.Log.Error(err)
		return fmt.Errorf("serial number run first. %s", err)
	}
	fmt.Println("Successfully Opened serialconfig.json")
	// defer the closing of our jsonFile so that we can parse it later on
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	var dat cmc.ConfigInstall //map[string]interface{}
	if err := json.Unmarshal(byteValue, &dat); err != nil {
		// panic(err)
		return err
	}
	cliinfo.Company, _ = dat.Results[0].GetCompanyID()
	cliinfo.Productid, _ = dat.Results[0].GetProductID()
	cliinfo.Solutionid, _ = dat.Results[0].GetSolutionID()

	jsonFile, err = os.Open("updatelist.json")
	// if we os.Open returns an error then handle it
	if err != nil {
		Log.Log.Error(err)
		return err
	}
	// defer the closing of our jsonFile so that we can parse it later on
	defer jsonFile.Close()
	var download cmcupdate.StatusResponse
	byteValue, _ = ioutil.ReadAll(jsonFile)
	if err = json.Unmarshal(byteValue, &download); err != nil {
		os.Exit(8)
	}

	sync := cmcupdate.SyncStatus{}

	if utils.FileExists("clientstatus.json") {
		jsonFile, err = os.Open("clientstatus.json")
		// if we os.Open returns an error then handle it
		if err != nil {
			Log.Log.Error(err)
			return err
		}
		// defer the closing of our jsonFile so that we can parse it later on
		defer jsonFile.Close()

		byteValue, _ = ioutil.ReadAll(jsonFile)
		if err = json.Unmarshal(byteValue, &sync); err != nil {
			Log.Log.Error(err)
		}
	} else {
		sync.Protocol = "2.0"
		sync.Client = cliinfo
	}

	sync.Sync.Status.Framework.Filelist = make([]map[string]interface{}, 0)
	if download.Framework.Version != "" {
		sync.Sync.Status.Framework.Version = download.Framework.Version
	}
	sync.Sync.Status.Phonedll.Deletelist = make([]interface{}, 0)
	sync.Sync.Status.Phonedll.Filelist = download.Phonedll.Filelist
	sync.Sync.Status.Phonetips.Deletelist = make([]interface{}, 0)
	sync.Sync.Status.Phonetips.Filelist = download.Phonetips.Filelist

	for i, v := range sync.Sync.Status.Phonedll.Filelist {
		delete(v, "url")
		sync.Sync.Status.Phonedll.Filelist[i] = v
	}
	for i, v := range sync.Sync.Status.Phonetips.Filelist {
		delete(v, "url")
		sync.Sync.Status.Phonedll.Filelist[i] = v
	}

	// file, _ := json.MarshalIndent(sync, "", " ")
	file, _ := json.Marshal(sync)
	_ = ioutil.WriteFile("clientstatus_temp.json", file, 0644)

	dmc.Set("hydradownload.clientstatus", string(file), 0)

	return nil
}

func main() {
	status, _ := dmc.GetString("hydradownload.status")
	if status == "pause" {
		os.Exit(0)
	}

	lock := fslock.New(".hydradownload.lock")
	err := lock.TryLock()
	if err != nil {
		fmt.Println(err.Error())
		return
	}

	defer lock.Unlock()

	dmc.Set("hydradownload.running", 1, 0)
	defer dmc.Set("hydradownload.running", 0, 0)

	Log.NewLogger("updatecmc")
	pathPtr := flag.String("path", "/opt/futuredial/hydradownloader", "download save folder")
	flag.Parse()

	faillist, err := cmcupdate.DownloadCMC(*pathPtr)

	if err != nil {
		_, err = cmcupdate.RetryDownload(faillist, *pathPtr)
	}
	if err != nil {
		dmc.Set("hydradownload.running", 0, 0)
		os.Exit(1)
	}
	if CreateClientStatus() != nil {
		dmc.Set("hydradownload.running", 0, 0)
		os.Exit(8)
	}
	dmc.Set("hydradownload.running", 0, 0)
	os.Exit(0)
}
